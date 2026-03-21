"""Unit tests for case selection functionality (Task 26.1)."""

import pytest
from case_manager import CaseManager


class TestCaseSelection:
    """Test case selection and listing functionality."""
    
    def test_list_available_cases(self):
        """Test that list_available_cases returns valid cases."""
        case_manager = CaseManager()
        available_cases = case_manager.list_available_cases()
        
        # Should have at least 2 cases (blackthorn-hall-001, digital-deception-002)
        assert len(available_cases) >= 2
        
        # Each entry should be (case_id, title) tuple
        for case_id, title in available_cases:
            assert isinstance(case_id, str)
            assert isinstance(title, str)
            assert len(case_id) > 0
            assert len(title) > 0
    
    def test_list_excludes_sample_case(self):
        """Test that sample_case.json is excluded from available cases."""
        case_manager = CaseManager()
        available_cases = case_manager.list_available_cases()
        
        # sample_case should not be in the list
        case_ids = [case_id for case_id, _ in available_cases]
        assert "sample_case" not in case_ids
    
    def test_load_case_from_list(self):
        """Test that cases from list can be loaded successfully."""
        case_manager = CaseManager()
        available_cases = case_manager.list_available_cases()
        
        assert len(available_cases) > 0, "No cases available for testing"
        
        # Try loading the first case
        case_id, expected_title = available_cases[0]
        case_content = case_manager.load_case(case_id)
        
        assert case_content.case_id == case_id
        assert case_content.title == expected_title
        assert len(case_content.evidence) >= 5
    
    def test_random_case_selection(self):
        """Test random case selection logic."""
        import random
        
        case_manager = CaseManager()
        available_cases = case_manager.list_available_cases()
        
        assert len(available_cases) > 0, "No cases available for testing"
        
        # Simulate random selection
        selected_case_id, selected_title = random.choice(available_cases)
        
        # Verify selected case can be loaded
        case_content = case_manager.load_case(selected_case_id)
        assert case_content.case_id == selected_case_id
        assert case_content.title == selected_title
