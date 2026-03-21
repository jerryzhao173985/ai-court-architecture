"""FastAPI application with REST endpoints and WebSocket support."""

from datetime import datetime
from typing import Optional, Literal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
import asyncio
import json

from models import CaseContent
from session import UserSession, SessionProgress, SessionMetadata, DeliberationTurn
from state_machine import ExperienceState, StateMachine
from case_manager import CaseManager
from orchestrator import ExperienceOrchestrator
from config import load_config


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    model_config = ConfigDict(populate_by_name=True)
    
    user_id: str = Field(alias="userId")
    case_id: str = Field(alias="caseId")


class CreateSessionResponse(BaseModel):
    """Response for session creation."""
    model_config = ConfigDict(populate_by_name=True)
    
    session_id: str = Field(alias="sessionId")
    case_id: str = Field(alias="caseId")
    current_state: str = Field(alias="currentState")
    message: str


class SessionStateResponse(BaseModel):
    """Response with session state."""
    model_config = ConfigDict(populate_by_name=True)
    
    session_id: str = Field(alias="sessionId")
    user_id: str = Field(alias="userId")
    case_id: str = Field(alias="caseId")
    current_state: str = Field(alias="currentState")
    progress: dict
    elapsed_time_seconds: float = Field(alias="elapsedTimeSeconds")


class SubmitStatementRequest(BaseModel):
    """Request to submit deliberation statement."""
    model_config = ConfigDict(populate_by_name=True)
    
    statement: str
    evidence_references: list[str] = Field(default_factory=list, alias="evidenceReferences")


class SubmitStatementResponse(BaseModel):
    """Response after submitting statement."""
    model_config = ConfigDict(populate_by_name=True)
    
    user_turn: dict = Field(alias="userTurn")
    ai_responses: list[dict] = Field(alias="aiResponses")


class SubmitVoteRequest(BaseModel):
    """Request to submit vote."""
    model_config = ConfigDict(populate_by_name=True)
    
    vote: Literal["guilty", "not_guilty"]


class SubmitVoteResponse(BaseModel):
    """Response after submitting vote."""
    model_config = ConfigDict(populate_by_name=True)
    
    verdict: str
    guilty_count: int = Field(alias="guiltyCount")
    not_guilty_count: int = Field(alias="notGuiltyCount")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="VERITAS Courtroom Experience API",
    description="Interactive courtroom trial experience with AI agents and jury deliberation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
active_sessions: dict[str, dict] = {}
case_manager = CaseManager()


# ============================================================================
# REST ENDPOINTS
# ============================================================================

@app.post("/api/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new experience session.
    
    Args:
        request: Session creation request
        
    Returns:
        Session creation response with session ID
    """
    try:
        session_id = f"session_{request.user_id}_{datetime.now().timestamp()}"

        # Create orchestrator (handles config loading internally)
        orchestrator = ExperienceOrchestrator(
            session_id=session_id,
            user_id=request.user_id,
            case_id=request.case_id
        )

        # Initialize experience
        result = await orchestrator.initialize()
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Initialization failed"))

        # Store session with orchestrator
        active_sessions[session_id] = {
            "orchestrator": orchestrator,
            "websocket_clients": []
        }

        return CreateSessionResponse(
            sessionId=session_id,
            caseId=request.case_id,
            currentState=ExperienceState.NOT_STARTED.value,
            message="Session created successfully"
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Case {request.case_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.get("/api/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str):
    """
    Retrieve session state.
    
    Args:
        session_id: The session ID
        
    Returns:
        Current session state
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = active_sessions[session_id]
    orchestrator: ExperienceOrchestrator = session_data["orchestrator"]

    elapsed = (datetime.now() - orchestrator.user_session.start_time).total_seconds()
    progress = orchestrator.get_progress()

    return SessionStateResponse(
        sessionId=orchestrator.session_id,
        userId=orchestrator.user_id,
        caseId=orchestrator.case_id,
        currentState=orchestrator.state_machine.current_state.value,
        progress=progress,
        elapsedTimeSeconds=elapsed
    )


@app.post("/api/sessions/{session_id}/statements", response_model=SubmitStatementResponse)
async def submit_statement(session_id: str, request: SubmitStatementRequest):
    """
    Submit user deliberation statement.
    
    Args:
        session_id: The session ID
        request: Statement submission request
        
    Returns:
        User turn and AI responses
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = active_sessions[session_id]
    orchestrator: ExperienceOrchestrator = session_data["orchestrator"]

    # Verify in deliberation state
    if orchestrator.state_machine.current_state != ExperienceState.JURY_DELIBERATION:
        raise HTTPException(status_code=400, detail="Not in deliberation state")

    # Submit through orchestrator
    result = await orchestrator.submit_deliberation_statement(
        request.statement,
        request.evidence_references
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to submit statement"))

    # Broadcast to WebSocket clients
    await broadcast_to_session(session_id, {
        "type": "deliberation_turn",
        "turns": result.get("turns", []),
        "deliberation_ended": result.get("deliberation_ended", False)
    })

    turns = result.get("turns", [])
    user_turn = turns[0] if turns else {}
    ai_responses = turns[1:] if len(turns) > 1 else []

    return SubmitStatementResponse(
        userTurn=user_turn,
        aiResponses=ai_responses
    )


@app.post("/api/sessions/{session_id}/vote", response_model=SubmitVoteResponse)
async def submit_vote(session_id: str, request: SubmitVoteRequest):
    """
    Submit user vote.
    
    Args:
        session_id: The session ID
        request: Vote submission request
        
    Returns:
        Vote result with verdict
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = active_sessions[session_id]
    orchestrator: ExperienceOrchestrator = session_data["orchestrator"]

    # Verify in voting state
    if orchestrator.state_machine.current_state != ExperienceState.ANONYMOUS_VOTE:
        raise HTTPException(status_code=400, detail="Not in voting state")

    # Submit through orchestrator
    result = await orchestrator.submit_vote(request.vote)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to submit vote"))

    dual_reveal = result.get("dual_reveal", {})
    verdict_data = dual_reveal.get("verdict", {})

    # Broadcast to WebSocket clients
    await broadcast_to_session(session_id, {
        "type": "vote_result",
        "dual_reveal": dual_reveal
    })

    return SubmitVoteResponse(
        verdict=verdict_data.get("verdict", "unknown"),
        guiltyCount=verdict_data.get("guiltyCount", 0),
        notGuiltyCount=verdict_data.get("notGuiltyCount", 0)
    )


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """
    Retrieve case content.
    
    Args:
        case_id: The case ID
        
    Returns:
        Case content
    """
    try:
        case_content = case_manager.load_case(case_id)
        return case_content.model_dump(by_alias=True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load case: {str(e)}")


@app.post("/api/sessions/{session_id}/start")
async def start_experience(session_id: str):
    """Start the experience (transition to hook scene)."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    orchestrator: ExperienceOrchestrator = active_sessions[session_id]["orchestrator"]
    result = await orchestrator.start_experience()

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to start"))

    await broadcast_to_session(session_id, {"type": "experience_started", "stage": result.get("stage")})
    return result


@app.post("/api/sessions/{session_id}/advance")
async def advance_stage(session_id: str):
    """Advance to the next trial stage."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    orchestrator: ExperienceOrchestrator = active_sessions[session_id]["orchestrator"]
    result = await orchestrator.advance_trial_stage()

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to advance"))

    await broadcast_to_session(session_id, {"type": "stage_advanced", "stage": result.get("stage")})
    return result


@app.post("/api/sessions/{session_id}/complete")
async def complete_experience(session_id: str, share_verdict: bool = False):
    """Complete the experience."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    orchestrator: ExperienceOrchestrator = active_sessions[session_id]["orchestrator"]
    result = await orchestrator.complete_experience(share_verdict)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to complete"))

    # Clean up session
    del active_sessions[session_id]
    return result


@app.get("/api/sessions/{session_id}/evidence")
async def get_evidence(session_id: str):
    """Get evidence board data."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    orchestrator: ExperienceOrchestrator = active_sessions[session_id]["orchestrator"]
    return orchestrator.get_evidence_board()


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket connection for real-time updates.
    
    Args:
        websocket: WebSocket connection
        session_id: The session ID
    """
    await websocket.accept()
    
    if session_id not in active_sessions:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return
    
    # Add client to session
    session_data = active_sessions[session_id]
    session_data["websocket_clients"].append(websocket)
    
    try:
        # Send initial state
        orchestrator: ExperienceOrchestrator = session_data["orchestrator"]
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "current_state": orchestrator.state_machine.current_state.value
        })

        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

            elif message.get("type") == "request_state":
                await websocket.send_json({
                    "type": "state_update",
                    "current_state": orchestrator.state_machine.current_state.value,
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        # Remove client from session
        session_data["websocket_clients"].remove(websocket)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


async def broadcast_to_session(session_id: str, message: dict):
    """
    Broadcast message to all WebSocket clients in a session.
    
    Args:
        session_id: The session ID
        message: Message to broadcast
    """
    if session_id not in active_sessions:
        return
    
    session_data = active_sessions[session_id]
    clients = session_data["websocket_clients"]
    
    # Send to all connected clients
    for client in list(clients):
        try:
            await client.send_json(message)
        except Exception as e:
            print(f"Failed to send to client: {e}")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
