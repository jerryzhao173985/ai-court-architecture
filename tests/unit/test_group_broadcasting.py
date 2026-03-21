"""Unit tests for group message broadcasting with visual formatting and buttons."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from state_machine import ExperienceState
from luffa_integration import LuffaBot
from models import CaseContent, CaseNarrative, CharacterProfile, GroundTruth, ReasoningCriteria, EvidenceItem
from luffa_client import LuffaAPIClient
from config import LuffaConfig


@pytest.fixture
def mock_case_content():
    """Create mock case content for testing."""
    # Create 5 evidence items to satisfy validation
    evidence_items = [
        EvidenceItem(
            id=f"evidence-{i}",
            type="physical",
            title=f"Evidence Item {i}",
            description=f"Test evidence {i}",
            timestamp="2024-01-01T10:00:00Z",
            presentedBy="prosecution",
            significance="Test significance"
        )
        for i in range(1, 6)
    ]
    
    return CaseContent(
        caseId="test-case-001",
        title="Test Case",
        narrative=CaseNarrative(
            hookScene="Test hook scene",
            chargeText="Test charge",
            victimProfile=CharacterProfile(
                name="Victim Name",
                role="victim",
                background="Test background",
                relevantFacts=[]
            ),
            defendantProfile=CharacterProfile(
                name="Defendant Name",
                role="defendant",
                background="Test background",
                relevantFacts=[]
            ),
            witnessProfiles=[]
        ),
        evidence=evidence_items,
        timeline=[],
        groundTruth=GroundTruth(
            actualVerdict="guilty",
            keyFacts=[],
            reasoningCriteria=ReasoningCriteria(
                requiredEvidenceReferences=[],
                logicalFallacies=[],
                coherenceThreshold=0.7
            )
        )
    )


@pytest.fixture
def mock_luffa_client():
    """Create mock Luffa API client."""
    client = AsyncMock(spec=LuffaAPIClient)
    client.send_group_message = AsyncMock(return_value={"success": True})
    return client


@pytest.fixture
def luffa_bot(mock_case_content, mock_luffa_client):
    """Create LuffaBot instance with mocked client."""
    return LuffaBot(mock_case_content, api_client=mock_luffa_client)


class TestStageAnnouncementFormatting:
    """Test visual formatting of stage announcements."""
    
    def test_hook_scene_announcement_has_emoji(self, luffa_bot):
        """Test hook scene announcement includes emoji."""
        message = luffa_bot.announce_stage(ExperienceState.HOOK_SCENE)
        assert "🎭" in message.content
        assert "THE TRIAL BEGINS" in message.content
    
    def test_charge_reading_announcement_has_emoji(self, luffa_bot):
        """Test charge reading announcement includes emoji."""
        message = luffa_bot.announce_stage(ExperienceState.CHARGE_READING)
        assert "⚖️" in message.content
        assert "CHARGE READING" in message.content
    
    def test_prosecution_opening_announcement_has_emoji(self, luffa_bot):
        """Test prosecution opening announcement includes emoji."""
        message = luffa_bot.announce_stage(ExperienceState.PROSECUTION_OPENING)
        assert "👔" in message.content
        assert "PROSECUTION OPENING" in message.content
    
    def test_defence_opening_announcement_has_emoji(self, luffa_bot):
        """Test defence opening announcement includes emoji."""
        message = luffa_bot.announce_stage(ExperienceState.DEFENCE_OPENING)
        assert "🛡️" in message.content
        assert "DEFENCE OPENING" in message.content
    
    def test_evidence_presentation_announcement_has_emoji(self, luffa_bot):
        """Test evidence presentation announcement includes emoji."""
        message = luffa_bot.announce_stage(ExperienceState.EVIDENCE_PRESENTATION)
        assert "📋" in message.content
        assert "EVIDENCE PRESENTATION" in message.content
    
    def test_jury_deliberation_announcement_has_emoji(self, luffa_bot):
        """Test jury deliberation announcement includes emoji."""
        message = luffa_bot.announce_stage(ExperienceState.JURY_DELIBERATION)
        assert "🗣️" in message.content
        assert "JURY DELIBERATION" in message.content
    
    def test_anonymous_vote_announcement_has_emoji(self, luffa_bot):
        """Test anonymous vote announcement includes emoji."""
        message = luffa_bot.announce_stage(ExperienceState.ANONYMOUS_VOTE)
        assert "🗳️" in message.content
        assert "TIME TO VOTE" in message.content
    
    def test_dual_reveal_announcement_has_emoji(self, luffa_bot):
        """Test dual reveal announcement includes emoji."""
        message = luffa_bot.announce_stage(ExperienceState.DUAL_REVEAL)
        assert "📊" in message.content
        assert "VERDICT REVEAL" in message.content
    
    def test_completed_announcement_has_emoji(self, luffa_bot):
        """Test completed announcement includes emoji."""
        message = luffa_bot.announce_stage(ExperienceState.COMPLETED)
        assert "✅" in message.content
        assert "TRIAL COMPLETE" in message.content


class TestGroupBroadcastingWithButtons:
    """Test group message broadcasting with interactive buttons."""
    
    @pytest.mark.asyncio
    async def test_broadcast_hook_scene_includes_continue_button(self, luffa_bot, mock_luffa_client):
        """Test hook scene broadcast includes continue button."""
        result = await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.HOOK_SCENE)
        
        assert result["success"] is True
        assert result["buttons_sent"] is True
        
        # Verify API was called with buttons
        mock_luffa_client.send_group_message.assert_called_once()
        call_args = mock_luffa_client.send_group_message.call_args
        
        assert call_args.kwargs["group_id"] == "test-group-id"
        assert "🎭" in call_args.kwargs["text"]
        assert call_args.kwargs["buttons"] is not None
        assert len(call_args.kwargs["buttons"]) == 1
        assert call_args.kwargs["buttons"][0]["name"] == "▶️ Continue"
        assert call_args.kwargs["buttons"][0]["selector"] == "/continue"
    
    @pytest.mark.asyncio
    async def test_broadcast_voting_includes_vote_buttons(self, luffa_bot, mock_luffa_client):
        """Test voting stage broadcast includes guilty/not guilty buttons."""
        result = await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.ANONYMOUS_VOTE)
        
        assert result["success"] is True
        assert result["buttons_sent"] is True
        
        # Verify API was called with vote buttons
        call_args = mock_luffa_client.send_group_message.call_args
        buttons = call_args.kwargs["buttons"]
        
        assert len(buttons) == 2
        assert buttons[0]["name"] == "✅ GUILTY"
        assert buttons[0]["selector"] == "/vote guilty"
        assert buttons[0]["isHidden"] == "1"  # Hidden from others
        
        assert buttons[1]["name"] == "❌ NOT GUILTY"
        assert buttons[1]["selector"] == "/vote not_guilty"
        assert buttons[1]["isHidden"] == "1"  # Hidden from others
    
    @pytest.mark.asyncio
    async def test_broadcast_deliberation_includes_evidence_button(self, luffa_bot, mock_luffa_client):
        """Test deliberation stage broadcast includes evidence button."""
        result = await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.JURY_DELIBERATION)
        
        assert result["success"] is True
        assert result["buttons_sent"] is True
        
        # Verify API was called with evidence button
        call_args = mock_luffa_client.send_group_message.call_args
        buttons = call_args.kwargs["buttons"]
        
        assert len(buttons) == 1
        assert buttons[0]["name"] == "📋 View Evidence"
        assert buttons[0]["selector"] == "/evidence"
        assert buttons[0]["isHidden"] == "0"  # Visible to all
    
    @pytest.mark.asyncio
    async def test_broadcast_trial_stages_include_continue_button(self, luffa_bot, mock_luffa_client):
        """Test all trial stages include continue button."""
        trial_stages = [
            ExperienceState.CHARGE_READING,
            ExperienceState.PROSECUTION_OPENING,
            ExperienceState.DEFENCE_OPENING,
            ExperienceState.EVIDENCE_PRESENTATION,
            ExperienceState.CROSS_EXAMINATION,
            ExperienceState.PROSECUTION_CLOSING,
            ExperienceState.DEFENCE_CLOSING,
            ExperienceState.JUDGE_SUMMING_UP
        ]
        
        for stage in trial_stages:
            mock_luffa_client.send_group_message.reset_mock()
            
            result = await luffa_bot.broadcast_stage_to_group("test-group-id", stage)
            
            assert result["success"] is True
            assert result["buttons_sent"] is True
            
            call_args = mock_luffa_client.send_group_message.call_args
            buttons = call_args.kwargs["buttons"]
            
            assert len(buttons) == 1
            assert buttons[0]["selector"] == "/continue"
    
    @pytest.mark.asyncio
    async def test_broadcast_dual_reveal_no_buttons(self, luffa_bot, mock_luffa_client):
        """Test dual reveal broadcast has no buttons."""
        result = await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.DUAL_REVEAL)
        
        assert result["success"] is True
        assert result["buttons_sent"] is False
        
        # Verify API was called without buttons
        call_args = mock_luffa_client.send_group_message.call_args
        assert call_args.kwargs["buttons"] is None
    
    @pytest.mark.asyncio
    async def test_broadcast_without_api_client_fails_gracefully(self, mock_case_content):
        """Test broadcasting without API client fails gracefully."""
        bot = LuffaBot(mock_case_content, api_client=None)
        
        result = await bot.broadcast_stage_to_group("test-group-id", ExperienceState.HOOK_SCENE)
        
        assert result["success"] is False
        assert "API client not initialized" in result["error"]
    
    @pytest.mark.asyncio
    async def test_broadcast_handles_api_errors(self, luffa_bot, mock_luffa_client):
        """Test broadcasting handles API errors gracefully."""
        mock_luffa_client.send_group_message.side_effect = Exception("API error")
        
        result = await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.HOOK_SCENE)
        
        assert result["success"] is False
        assert "API error" in result["error"]


class TestButtonConfiguration:
    """Test button configuration for different stages."""
    
    @pytest.mark.asyncio
    async def test_continue_buttons_visible_to_all(self, luffa_bot, mock_luffa_client):
        """Test continue buttons are visible to all users."""
        await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.HOOK_SCENE)
        
        call_args = mock_luffa_client.send_group_message.call_args
        buttons = call_args.kwargs["buttons"]
        
        assert buttons[0]["isHidden"] == "0"
    
    @pytest.mark.asyncio
    async def test_vote_buttons_hidden_from_others(self, luffa_bot, mock_luffa_client):
        """Test vote buttons are hidden from other users."""
        await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.ANONYMOUS_VOTE)
        
        call_args = mock_luffa_client.send_group_message.call_args
        buttons = call_args.kwargs["buttons"]
        
        for button in buttons:
            assert button["isHidden"] == "1"
    
    @pytest.mark.asyncio
    async def test_buttons_use_select_dismiss_type(self, luffa_bot, mock_luffa_client):
        """Test buttons use 'select' dismiss type to persist."""
        await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.HOOK_SCENE)
        
        call_args = mock_luffa_client.send_group_message.call_args
        assert call_args.kwargs["dismiss_type"] == "select"


class TestStageTransitionBroadcasting:
    """Test broadcasting during stage transitions."""
    
    @pytest.mark.asyncio
    async def test_broadcast_includes_stage_metadata(self, luffa_bot, mock_luffa_client):
        """Test broadcast result includes stage metadata."""
        result = await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.HOOK_SCENE)
        
        assert result["stage"] == ExperienceState.HOOK_SCENE.value
        assert "message" in result
        assert result["message"] == luffa_bot.announce_stage(ExperienceState.HOOK_SCENE).content
    
    @pytest.mark.asyncio
    async def test_broadcast_returns_api_response(self, luffa_bot, mock_luffa_client):
        """Test broadcast returns API response."""
        mock_luffa_client.send_group_message.return_value = {"success": True, "msgId": "123"}
        
        result = await luffa_bot.broadcast_stage_to_group("test-group-id", ExperienceState.HOOK_SCENE)
        
        assert "api_response" in result
        assert result["api_response"]["success"] is True
        assert result["api_response"]["msgId"] == "123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
