"""Unit tests for prosecution/defence emphasis variation (Task 26.3)."""

import pytest
from trial_orchestrator import TrialOrchestrator
from case_manager import CaseManager


class TestEmphasisVariation:
    """Test emphasis item selection for trial variation."""
    
    def test_emphasis_items_selected(self):
        """Test that emphasis items are selected during initialization."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        orchestrator = TrialOrchestrator()
        orchestrator.initialize_agents(case_content)
        
        # Should have emphasis items selected
        assert hasattr(orchestrator, 'emphasis_items')
        assert len(orchestrator.emphasis_items) > 0
        assert len(orchestrator.emphasis_items) <= 3
        
        # All emphasis items should be from the case evidence
        evidence_titles = {e.title for e in case_content.evidence}
        for item in orchestrator.emphasis_items:
            assert item.title in evidence_titles
    
    def test_prosecution_prompt_includes_emphasis(self):
        """Test that prosecution prompt includes emphasis section."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        orchestrator = TrialOrchestrator()
        orchestrator.initialize_agents(case_content)
        
        # Get prosecution agent
        prosecution_agent = orchestrator.agents["prosecution"]
        
        # Prompt should include emphasis section
        assert "EMPHASIZE THESE ITEMS MOST STRONGLY:" in prosecution_agent.system_prompt
        
        # Should mention at least one emphasis item
        for item in orchestrator.emphasis_items:
            assert item.title in prosecution_agent.system_prompt
    
    def test_defence_prompt_includes_prosecution_focus(self):
        """Test that defence prompt includes prosecution focus awareness."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        orchestrator = TrialOrchestrator()
        orchestrator.initialize_agents(case_content)
        
        # Get defence agent
        defence_agent = orchestrator.agents["defence"]
        
        # Prompt should include prosecution focus section
        assert "THE PROSECUTION WILL FOCUS ON:" in defence_agent.system_prompt
        
        # Should mention at least one emphasis item
        for item in orchestrator.emphasis_items:
            assert item.title in defence_agent.system_prompt
    
    def test_emphasis_variation_across_trials(self):
        """Test that different trials can have different emphasis items."""
        case_manager = CaseManager()
        case_content = case_manager.load_case("blackthorn-hall-001")
        
        # Run multiple initializations
        emphasis_sets = []
        for _ in range(5):
            orchestrator = TrialOrchestrator()
            orchestrator.initialize_agents(case_content)
            
            # Store the set of emphasis item titles
            emphasis_titles = {item.title for item in orchestrator.emphasis_items}
            emphasis_sets.append(emphasis_titles)
        
        # At least some variation should occur (not all identical)
        # With random selection, it's very unlikely all 5 are identical
        unique_sets = len(set(frozenset(s) for s in emphasis_sets))
        assert unique_sets > 1, "Expected some variation in emphasis items across trials"
