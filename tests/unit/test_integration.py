"""Integration tests for VERITAS components."""

import pytest
from src.orchestrator import ExperienceOrchestrator
from src.evidence_board import EvidenceBoard
from src.trial_orchestrator import TrialOrchestrator
from src.jury_orchestrator import JuryOrchestrator
from src.reasoning_evaluator import ReasoningEvaluator
from src.dual_reveal import DualRevealAssembler
from src.trial_stages import TrialStageManager
from src.luffa_integration import LuffaBot, SuperBox, LuffaChannel
from src.case_manager import CaseManager
from src.state_machine import ExperienceState


class TestComponentInitialization:
    """Test that all components can be initialized."""

    def test_case_manager_loads_blackthorn_hall(self):
        """Test case manager can load Blackthorn Hall case."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        assert case_content.case_id == "blackthorn-hall-001"
        assert case_content.title is not None
        assert len(case_content.evidence) >= 5
        assert len(case_content.evidence) <= 7

    def test_evidence_board_initialization(self):
        """Test evidence board can be initialized with case content."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        evidence_board = EvidenceBoard(case_content)
        
        assert evidence_board.items == case_content.evidence
        assert evidence_board.timeline == case_content.timeline
        assert evidence_board.is_accessible()

    def test_evidence_board_timeline_rendering(self):
        """Test evidence board renders timeline."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        evidence_board = EvidenceBoard(case_content)
        timeline = evidence_board.render_timeline()
        
        assert len(timeline) == len(case_content.evidence)
        assert all("timestamp" in item for item in timeline)
        assert all("evidence_id" in item for item in timeline)

    def test_trial_orchestrator_initialization(self):
        """Test trial orchestrator initializes 5 agents."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        orchestrator = TrialOrchestrator()
        orchestrator.initialize_agents(case_content)
        
        assert len(orchestrator.agents) == 5
        assert "clerk" in orchestrator.agents
        assert "prosecution" in orchestrator.agents
        assert "defence" in orchestrator.agents
        assert "fact_checker" in orchestrator.agents
        assert "judge" in orchestrator.agents

    def test_jury_orchestrator_initialization(self):
        """Test jury orchestrator initializes 8 jurors."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        orchestrator = JuryOrchestrator()
        orchestrator.initialize_jury(case_content)
        
        assert len(orchestrator.jurors) == 8
        
        # Check 3 active AI jurors
        active_ai = [j for j in orchestrator.jurors if j.type == "active_ai"]
        assert len(active_ai) == 3
        
        # Check personas
        personas = [j.persona for j in active_ai]
        assert "evidence_purist" in personas
        assert "sympathetic_doubter" in personas
        assert "moral_absolutist" in personas
        
        # Check 4 lightweight AI jurors
        lightweight = [j for j in orchestrator.jurors if j.type == "lightweight_ai"]
        assert len(lightweight) == 4
        
        # Check 1 human juror
        human = [j for j in orchestrator.jurors if j.type == "human"]
        assert len(human) == 1

    def test_reasoning_evaluator_initialization(self):
        """Test reasoning evaluator can be initialized."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        evaluator = ReasoningEvaluator(case_content)
        
        assert evaluator.case_content == case_content
        assert evaluator.ground_truth == case_content.ground_truth

    def test_dual_reveal_assembler_initialization(self):
        """Test dual reveal assembler can be initialized."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        assembler = DualRevealAssembler(case_content)
        
        assert assembler.case_content == case_content

    def test_trial_stage_manager_initialization(self):
        """Test trial stage manager can be initialized."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        manager = TrialStageManager(case_content)
        
        assert manager.case_content == case_content

    def test_trial_stage_manager_hook_scene(self):
        """Test trial stage manager presents hook scene."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        manager = TrialStageManager(case_content)
        hook_content = manager.present_hook_scene()
        
        assert hook_content.stage == ExperienceState.HOOK_SCENE
        assert hook_content.content is not None
        assert 60 <= hook_content.duration_seconds <= 90

    def test_luffa_bot_initialization(self):
        """Test Luffa Bot can be initialized."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        bot = LuffaBot(case_content)
        greeting = bot.get_greeting()
        
        assert greeting.type == "greeting"
        assert greeting.content is not None

    def test_superbox_initialization(self):
        """Test SuperBox can be initialized."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        superbox = SuperBox(case_content)
        scene = superbox.render_courtroom_scene()
        
        assert scene.scene_type == "courtroom"
        assert len(scene.elements) > 0

    def test_luffa_channel_initialization(self):
        """Test Luffa Channel can be initialized."""
        channel = LuffaChannel()
        
        assert channel.verdict_shares == []


@pytest.mark.asyncio
class TestOrchestratorIntegration:
    """Test orchestrator integration."""

    async def test_orchestrator_initialization(self):
        """Test orchestrator can initialize all components."""
        orchestrator = ExperienceOrchestrator(
            session_id="test_session",
            user_id="test_user",
            case_id="blackthorn-hall-001"
        )
        
        result = await orchestrator.initialize()
        
        assert result["success"] is True
        assert result["session_id"] == "test_session"
        assert "greeting" in result

    async def test_orchestrator_start_experience(self):
        """Test orchestrator can start experience."""
        orchestrator = ExperienceOrchestrator(
            session_id="test_session",
            user_id="test_user",
            case_id="blackthorn-hall-001"
        )
        
        await orchestrator.initialize()
        result = await orchestrator.start_experience()
        
        assert result["success"] is True
        assert result["stage"] == ExperienceState.HOOK_SCENE.value

    async def test_orchestrator_evidence_board_access(self):
        """Test orchestrator provides evidence board access."""
        orchestrator = ExperienceOrchestrator(
            session_id="test_session",
            user_id="test_user",
            case_id="blackthorn-hall-001"
        )
        
        await orchestrator.initialize()
        evidence_board = orchestrator.get_evidence_board()
        
        assert "timeline" in evidence_board
        assert "items" in evidence_board
        assert len(evidence_board["items"]) >= 5

    async def test_orchestrator_progress_tracking(self):
        """Test orchestrator tracks progress."""
        orchestrator = ExperienceOrchestrator(
            session_id="test_session",
            user_id="test_user",
            case_id="blackthorn-hall-001"
        )
        
        await orchestrator.initialize()
        await orchestrator.start_experience()
        
        progress = orchestrator.get_progress()
        
        assert "current_stage" in progress
        assert "progress_percentage" in progress
        assert progress["current_stage"] == ExperienceState.HOOK_SCENE.value
