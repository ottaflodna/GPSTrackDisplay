"""
Abstract base window class for track visualization applications
Provides common functionality for managing tracks and viewer integration
"""

from abc import ABCMeta, abstractmethod
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from typing import List, Optional

from models.track import Track
from ui.track_manager_widget import TrackManagerWidget
from viewer.base_viewer import BaseViewer


# Combined metaclass for QMainWindow and ABC compatibility
class QABCMeta(type(QMainWindow), ABCMeta):
    """Metaclass that combines Qt's meta-object system with ABC"""
    pass


class BaseWindow(QMainWindow, metaclass=QABCMeta):
    """
    Abstract base window for track visualization applications
    
    Subclasses must implement:
    - create_viewer(): Return a viewer instance
    - setup_viewer_widget(): Setup the central widget for displaying the view
    - setup_viewer_properties_dock(): Setup viewer-specific property controls
    - on_viewer_properties_changed(): Handle property changes
    """
    
    def __init__(self):
        super().__init__()
        self.tracks: List[Track] = []
        self.viewer: Optional[BaseViewer] = None
        self.current_view_file: Optional[str] = None
        self.view_state: dict = {}  # Stores viewer state (center, zoom, etc.)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main window UI (common for all applications)"""
        self.setMinimumSize(1000, 700)
        
        # Create central widget for viewer
        self.setup_viewer_widget()
        
        # Create track manager dock
        self.setup_track_manager_dock()
        
        # Create viewer-specific properties dock (implemented by subclass)
        self.setup_viewer_properties_dock()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Create viewer instance
        self.viewer = self.create_viewer()
        
        # Initialize empty view
        self.initialize_empty_view()
    
    @abstractmethod
    def create_viewer(self) -> BaseViewer:
        """
        Create and return the viewer instance for this application
        Must be implemented by subclass
        """
        pass
    
    @abstractmethod
    def setup_viewer_widget(self):
        """
        Setup the central widget for displaying the view
        Must be implemented by subclass
        """
        pass
    
    @abstractmethod
    def setup_viewer_properties_dock(self):
        """
        Setup viewer-specific property controls in a dock widget
        Must be implemented by subclass
        """
        pass
    
    @abstractmethod
    def on_viewer_properties_changed(self, fit_bounds: bool = False):
        """
        Handle viewer property changes and regenerate view
        Must be implemented by subclass
        
        Args:
            fit_bounds: If True, recalculates view bounds to fit all tracks
        """
        pass
    
    @abstractmethod
    def load_view_in_widget(self, view_file: str):
        """
        Load the generated view file in the viewer widget
        Must be implemented by subclass
        
        Args:
            view_file: Path to the view file to load
        """
        pass
    
    @abstractmethod
    def initialize_empty_view(self):
        """
        Initialize an empty view (when no tracks are loaded)
        Must be implemented by subclass
        """
        pass
    
    def setup_track_manager_dock(self):
        """Setup the track manager dock widget (common for all applications)"""
        self.track_manager = TrackManagerWidget("Active Tracklogs", self)
        
        # Connect signals
        self.track_manager.tracks_changed.connect(self.on_tracks_changed)
        self.track_manager.track_properties_changed.connect(self.on_track_properties_changed)
        
        # Add to window (left side by default)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.track_manager)
    
    def on_tracks_changed(self, tracks: List[Track]):
        """
        Handle tracks being added/removed/cleared
        
        Args:
            tracks: Updated list of all tracks
        """
        self.tracks = tracks
        
        if len(self.tracks) == 0:
            # No tracks - show empty view
            self.initialize_empty_view()
            self.view_state = {}
        else:
            # Regenerate view with zoom recalculation
            self.on_viewer_properties_changed(fit_bounds=True)
    
    def on_track_properties_changed(self):
        """Handle track property changes (name, color, width)"""
        # Preserve view state when only properties change
        self.on_viewer_properties_changed(fit_bounds=False)
    
    def get_viewer_options(self) -> dict:
        """
        Get current viewer options from UI controls
        Should be overridden by subclass to return actual options
        
        Returns:
            Dictionary of viewer options
        """
        return {}
    
    def regenerate_view(self, fit_bounds: bool = False):
        """
        Regenerate the view with current tracks and settings
        
        Args:
            fit_bounds: If True, recalculates view bounds to fit all tracks
        """
        try:
            if not self.viewer:
                return
            
            if not self.tracks:
                # No tracks - show empty view
                self.initialize_empty_view()
                self.view_state = {}
                self.statusBar().showMessage("View reset (no tracks)")
                return
            
            self.statusBar().showMessage("Generating view...")
            
            # Get viewer options from subclass
            options = self.get_viewer_options()
            options['fit_bounds'] = fit_bounds
            
            # Pass current view state if not fitting bounds
            if not fit_bounds and self.view_state:
                options.update(self.view_state)
            
            # Generate view
            view_file, new_view_state = self.viewer.create_view(
                self.tracks,
                output_file=self.get_default_output_file(),
                **options
            )
            
            self.current_view_file = view_file
            self.view_state = new_view_state
            
            # Load view in widget
            self.load_view_in_widget(view_file)
            
            zoom_msg = " (bounds adjusted)" if fit_bounds else " (view preserved)"
            self.statusBar().showMessage(
                f"View generated with {len(self.tracks)} track(s){zoom_msg}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Error generating view:\n{str(e)}"
            )
            self.statusBar().showMessage("Error generating view")
    
    def get_default_output_file(self) -> str:
        """
        Get default output filename for the view
        Can be overridden by subclass
        """
        return "track_view.html"
    
    def set_initial_tracks(self, tracks: List[Track]):
        """
        Set initial tracks (e.g., from command line arguments)
        
        Args:
            tracks: List of tracks to load initially
        """
        self.track_manager.set_tracks(tracks)
