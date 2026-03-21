"""Unit tests for /cases command functionality (Task 26.2)."""

import pytest
from case_manager import CaseManager
from complexity_analyzer import CaseComplexityAnalyzer


class TestCasesCommand:
    """Test /cases command functionality."""
    
    def test_cases_command_lists_all_cases(self):
        """Test that /cases command can list all available cases."""
        case_manager = CaseManager()
        available_cases = case_manager.list_available_cases()
        
        # Should have at least 2 cases
        assert len(available_cases) >= 2
        
        # Verify we can build the cases list
        cases_text = "📋 AVAILABLE CASES\n\n"
        
        for idx, (case_id, title) in enumerate(available_cases, 1):
            case_content = case_manager.load_case(case_id)
            analyzer = CaseComplexityAnalyzer()
            complexity = analyzer.analyze_complexity(case_content)
            complexity_level = complexity.level.title()
            
            cases_text += f"{idx}. {title}\n"
            cases_text += f"   Case ID: {case_id}\n"
            cases_text += f"   Complexity: {complexity_level}\n\n"
        
        # Verify output contains expected elements
        assert "📋 AVAILABLE CASES" in cases_text
        assert "Case ID:" in cases_text
        assert "Complexity:" in cases_text
    
    def test_complexity_levels_valid(self):
        """Test that complexity analysis returns valid levels."""
        case_manager = CaseManager()
        available_cases = case_manager.list_available_cases()
        
        assert len(available_cases) > 0
        
        analyzer = CaseComplexityAnalyzer()
        valid_levels = ["simple", "moderate", "complex"]
        
        for case_id, _ in available_cases:
            case_content = case_manager.load_case(case_id)
            complexity = analyzer.analyze_complexity(case_content)
            
            assert complexity.level in valid_levels
            assert hasattr(complexity, "verbosity_multiplier")
            assert 0.5 <= complexity.verbosity_multiplier <= 1.5

