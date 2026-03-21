"""Evidence board component for displaying and interacting with case evidence."""

from typing import Optional
from models import EvidenceItem, TimelineEvent, CaseContent


class EvidenceBoard:
    """
    Visual interface for displaying and interacting with case evidence.
    
    Provides chronological timeline rendering, highlighting, selection,
    and filtering of evidence items during trial and deliberation.
    """

    def __init__(self, case_content: CaseContent):
        """
        Initialize evidence board with case content.
        
        Args:
            case_content: The case content containing evidence and timeline
        """
        self.items = case_content.evidence
        self.timeline = case_content.timeline
        self.highlighted_item_id: Optional[str] = None
        self._sorted_items = sorted(self.items, key=lambda item: item.timestamp)

    def render_timeline(self) -> list[dict]:
        """
        Render chronological evidence timeline.
        
        Returns:
            List of timeline entries with evidence items positioned at timestamps
        """
        timeline_data = []
        
        for item in self._sorted_items:
            timeline_data.append({
                "timestamp": item.timestamp,
                "evidence_id": item.id,
                "title": item.title,
                "type": item.type,
                "highlighted": item.id == self.highlighted_item_id
            })
        
        return timeline_data

    def highlight_item(self, item_id: str) -> None:
        """
        Highlight an evidence item (e.g., when presented during trial).
        
        Args:
            item_id: The ID of the evidence item to highlight
        """
        self.highlighted_item_id = item_id

    def select_item(self, item_id: str) -> Optional[EvidenceItem]:
        """
        Select an evidence item for detailed view.
        
        Args:
            item_id: The ID of the evidence item to select
            
        Returns:
            The selected EvidenceItem or None if not found
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def filter_by_type(self, evidence_type: str) -> list[EvidenceItem]:
        """
        Filter evidence items by type.
        
        Args:
            evidence_type: Type to filter by ("physical", "testimonial", "documentary")
            
        Returns:
            List of evidence items matching the type
        """
        return [item for item in self.items if item.type == evidence_type]

    def search_evidence(self, query: str) -> list[EvidenceItem]:
        """
        Search evidence items by keyword.
        
        Args:
            query: Search query string
            
        Returns:
            List of evidence items matching the query
        """
        query_lower = query.lower()
        results = []
        
        for item in self.items:
            if (query_lower in item.title.lower() or
                query_lower in item.description.lower() or
                query_lower in item.significance.lower()):
                results.append(item)
        
        return results

    def get_all_items(self) -> list[EvidenceItem]:
        """
        Get all evidence items.
        
        Returns:
            List of all evidence items
        """
        return self.items

    def is_accessible(self) -> bool:
        """
        Check if evidence board is accessible.
        
        Returns:
            True (evidence board is always accessible once initialized)
        """
        return True
