"""
Abstract base class for all viewer types (map, curve, etc.)
Defines common interface that all viewers must implement
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models.track import Track


class BaseViewer(ABC):
    """Abstract base class for track viewers"""
    
    @abstractmethod
    def create_view(self, tracks: List[Track], output_file: str, **kwargs) -> tuple:
        """
        Create a view with the given tracks
        
        Args:
            tracks: List of Track objects to display
            output_file: Output file path for the view
            **kwargs: Viewer-specific options
            
        Returns:
            Tuple containing (file_path, view_state_dict)
            view_state_dict contains any state needed to preserve the view
        """
        pass
    
    @abstractmethod
    def get_available_options(self) -> Dict[str, Any]:
        """
        Get available configuration options for this viewer type
        
        Returns:
            Dictionary of option names to their configurations
            Example: {'base_layer': {'type': 'combo', 'values': ['Topo', 'Satellite']}}
        """
        pass
    
    @abstractmethod
    def get_default_options(self) -> Dict[str, Any]:
        """
        Get default values for all options
        
        Returns:
            Dictionary of option names to default values
        """
        pass
    
    def validate_tracks(self, tracks: List[Track]) -> bool:
        """
        Validate that tracks are suitable for this viewer
        Can be overridden by subclasses
        
        Args:
            tracks: List of tracks to validate
            
        Returns:
            True if tracks are valid for this viewer
        """
        return tracks is not None and len(tracks) > 0
    
    def get_required_track_attributes(self) -> List[str]:
        """
        Get list of required track point attributes for this viewer
        Can be overridden by subclasses
        
        Returns:
            List of required attribute names (e.g., ['altitude', 'timestamp'])
        """
        return []
