"""
Map Application - GPS Track Map Viewer
Uses the refactored base classes and reusable components
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout,
                             QComboBox, QCheckBox, QDoubleSpinBox, QFileDialog,
                             QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QEventLoop, QTimer
from typing import List
import os
import json
from datetime import datetime

from ui.base_window import BaseWindow
from viewer.base_viewer import BaseViewer
from viewer.map_viewer import MapViewer
from models.track import Track


class MapWindow(BaseWindow):
    """Main window for GPS tracklog map viewer"""
    
    def __init__(self):
        # Initialize map-specific properties before calling super().__init__()
        self.base_map = "OpenTopoMap"
        self.track_color_mode = "Plain"
        self.colormap = "Jet (Blue-Green-Yellow-Red)"  # Default colormap
        self.show_start_stop = False
        self.show_legend = False
        self.show_zoom_controls = False
        self.color_min = None
        self.color_max = None
        
        super().__init__()
        self.setWindowTitle("GPS Tracklog Map Viewer")
        
        # Add screenshot button to track manager (after it's created)
        from PyQt5.QtWidgets import QPushButton
        screenshot_btn = QPushButton("Screenshot")
        screenshot_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        screenshot_btn.clicked.connect(self.take_screenshot)
        self.track_manager.widget().layout().addWidget(screenshot_btn)
    
    def create_viewer(self) -> BaseViewer:
        """Create and return the map viewer instance"""
        return MapViewer()
    
    def setup_viewer_widget(self):
        """Setup the map display as central widget"""
        central_widget = QWidget()
        map_layout = QVBoxLayout()
        central_widget.setLayout(map_layout)
        
        # Web view for map
        self.map_view = QWebEngineView()
        map_layout.addWidget(self.map_view)
        
        # Set as central widget
        self.setCentralWidget(central_widget)
    
    def setup_viewer_properties_dock(self):
        """Setup the map properties dock widget"""
        from PyQt5.QtWidgets import QDockWidget
        
        # Create dock widget
        properties_dock = QDockWidget("Map Properties", self)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        
        # Create properties widget
        properties_widget = QWidget()
        properties_layout = QFormLayout()
        properties_widget.setLayout(properties_layout)
        
        # Base map settings group
        map_groupbox = QGroupBox("Base map settings")
        map_layout = QFormLayout()
        map_groupbox.setLayout(map_layout)
        properties_layout.addRow(map_groupbox)
        
        # Base map selector
        self.base_map_combo = QComboBox()
        self.base_map_combo.addItems(MapViewer.AVAILABLE_BASE_MAPS)
        self.base_map_combo.setCurrentText(self.base_map)
        self.base_map_combo.currentTextChanged.connect(self.on_base_map_changed)
        map_layout.addRow("Base map:", self.base_map_combo)
        
        # Track color settings group
        track_groupbox = QGroupBox("Track color settings")
        track_layout = QFormLayout()
        track_groupbox.setLayout(track_layout)
        properties_layout.addRow(track_groupbox)
        
        # Track color mode selector
        self.track_color_combo = QComboBox()
        self.track_color_combo.addItems(MapViewer.COLOR_MODES)
        self.track_color_combo.setCurrentText(self.track_color_mode)
        self.track_color_combo.currentTextChanged.connect(self.on_track_color_changed)
        track_layout.addRow("Track color:", self.track_color_combo)
        
        # Colormap selector
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(MapViewer.AVAILABLE_COLORMAPS)
        self.colormap_combo.setCurrentText(self.colormap)
        self.colormap_combo.setEnabled(False)  # Disabled by default (enabled when color mode is not Plain)
        self.colormap_combo.currentTextChanged.connect(self.on_colormap_changed)
        track_layout.addRow("Colormap:", self.colormap_combo)
        
        # Color scale min/max inputs
        self.color_min_spinbox = QDoubleSpinBox()
        self.color_min_spinbox.setRange(-999999, 999999)
        self.color_min_spinbox.setDecimals(2)
        self.color_min_spinbox.setEnabled(False)
        self.color_min_spinbox.editingFinished.connect(self.on_color_min_changed)
        track_layout.addRow("Color min:", self.color_min_spinbox)
        
        self.color_max_spinbox = QDoubleSpinBox()
        self.color_max_spinbox.setRange(-999999, 999999)
        self.color_max_spinbox.setDecimals(2)
        self.color_max_spinbox.setEnabled(False)
        self.color_max_spinbox.editingFinished.connect(self.on_color_max_changed)
        track_layout.addRow("Color max:", self.color_max_spinbox)
        
        # Display settings group
        display_groupbox = QGroupBox("Viewer display settings")
        display_layout = QFormLayout()
        display_groupbox.setLayout(display_layout)
        properties_layout.addRow(display_groupbox)
        
        # Show start/stop checkbox
        self.show_start_stop_checkbox = QCheckBox()
        self.show_start_stop_checkbox.setChecked(self.show_start_stop)
        self.show_start_stop_checkbox.stateChanged.connect(self.on_show_start_stop_changed)
        display_layout.addRow("Show start and stop:", self.show_start_stop_checkbox)
        
        # Show legend checkbox
        self.show_legend_checkbox = QCheckBox()
        self.show_legend_checkbox.setChecked(self.show_legend)
        self.show_legend_checkbox.stateChanged.connect(self.on_show_legend_changed)
        display_layout.addRow("Show legend:", self.show_legend_checkbox)
        
        # Show zoom controls checkbox
        self.show_zoom_controls_checkbox = QCheckBox()
        self.show_zoom_controls_checkbox.setChecked(self.show_zoom_controls)
        self.show_zoom_controls_checkbox.stateChanged.connect(self.on_show_zoom_controls_changed)
        display_layout.addRow("Show zoom controls:", self.show_zoom_controls_checkbox)
        
        # Set widget to dock
        properties_dock.setWidget(properties_widget)
        
        # Add dock to main window on left side, below tracks dock
        self.addDockWidget(Qt.LeftDockWidgetArea, properties_dock)
        self.splitDockWidget(self.track_manager, properties_dock, Qt.Vertical)
    
    def on_base_map_changed(self, value: str):
        """Handle base map selection change"""
        self.base_map = value
        self.statusBar().showMessage(f"Base map set to: {value}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
        else:
            self.initialize_empty_view()
    
    def on_track_color_changed(self, value: str):
        """Handle track color mode change"""
        self.track_color_mode = value
        
        # Compute min/max values for the selected color mode
        if value != "Plain" and self.tracks:
            computed_min, computed_max = self.viewer._get_value_range(self.tracks, value)
            self.color_min = computed_min
            self.color_max = computed_max
            
            # Update spinboxes
            self.color_min_spinbox.blockSignals(True)
            self.color_max_spinbox.blockSignals(True)
            self.color_min_spinbox.setValue(computed_min)
            self.color_max_spinbox.setValue(computed_max)
            self.color_min_spinbox.blockSignals(False)
            self.color_max_spinbox.blockSignals(False)
            
            # Enable spinboxes and colormap
            self.color_min_spinbox.setEnabled(True)
            self.color_max_spinbox.setEnabled(True)
            self.colormap_combo.setEnabled(True)
        else:
            self.color_min = None
            self.color_max = None
            self.color_min_spinbox.setEnabled(False)
            self.color_max_spinbox.setEnabled(False)
            self.colormap_combo.setEnabled(False)
        
        self.statusBar().showMessage(f"Track color mode set to: {value}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_color_min_changed(self):
        """Handle color min value change"""
        self.color_min = self.color_min_spinbox.value()
        self.statusBar().showMessage(f"Color min set to: {self.color_min:.2f}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_color_max_changed(self):
        """Handle color max value change"""
        self.color_max = self.color_max_spinbox.value()
        self.statusBar().showMessage(f"Color max set to: {self.color_max:.2f}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_colormap_changed(self, value: str):
        """Handle colormap selection change"""
        self.colormap = value
        self.statusBar().showMessage(f"Colormap set to: {value}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_show_start_stop_changed(self, state: int):
        """Handle show start/stop checkbox change"""
        self.show_start_stop = (state == Qt.Checked)
        self.statusBar().showMessage(f"Start/stop markers: {'On' if self.show_start_stop else 'Off'}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_show_legend_changed(self, state: int):
        """Handle show legend checkbox change"""
        self.show_legend = (state == Qt.Checked)
        self.statusBar().showMessage(f"Legend: {'On' if self.show_legend else 'Off'}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_show_zoom_controls_changed(self, state: int):
        """Handle show zoom controls checkbox change"""
        self.show_zoom_controls = (state == Qt.Checked)
        self.statusBar().showMessage(f"Zoom controls: {'On' if self.show_zoom_controls else 'Off'}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
        else:
            self.initialize_empty_view()
    
    def on_viewer_properties_changed(self, fit_bounds: bool = False):
        """Handle viewer property changes and regenerate map"""
        # Capture current view before regenerating (if not fitting bounds)
        if not fit_bounds and self.current_view_file and self.tracks:
            self._capture_current_view()
        
        self.regenerate_view(fit_bounds)
    
    def get_viewer_options(self) -> dict:
        """Get current viewer options from UI controls"""
        return {
            'base_map': self.base_map,
            'color_mode': self.track_color_mode,
            'colormap': self.colormap,
            'show_start_stop': self.show_start_stop,
            'show_legend': self.show_legend,
            'zoom_control': self.show_zoom_controls,
            'color_min': self.color_min,
            'color_max': self.color_max
        }
    
    def load_view_in_widget(self, view_file: str):
        """Load the map HTML file in the web view"""
        if os.path.exists(view_file):
            url = QUrl.fromLocalFile(os.path.abspath(view_file))
            self.map_view.setUrl(url)
            self.map_view.reload()
    
    def initialize_empty_view(self):
        """Initialize an empty map centered on Lausanne"""
        import folium
        
        # Lausanne coordinates
        lausanne_coords = [46.5197, 6.6323]
        
        # Create empty map with selected base layer
        m = self.viewer._create_base_map(
            lausanne_coords, 
            self.base_map, 
            zoom_control=self.show_zoom_controls
        )
        
        # Save map
        map_file = os.path.abspath('track_map.html')
        m.save(map_file)
        self.current_view_file = map_file
        
        # Load in view
        self.load_view_in_widget(map_file)
    
    def get_default_output_file(self) -> str:
        """Get default output filename for the map"""
        return "track_map.html"
    
    def _capture_current_view(self):
        """Capture the current map center and zoom from the browser"""
        # JavaScript to extract Leaflet map's current view
        js_code = """
        (function() {
            try {
                var map = null;
                for (var key in window) {
                    if (window[key] && window[key]._layers) {
                        map = window[key];
                        break;
                    }
                }
                if (map) {
                    var center = map.getCenter();
                    var zoom = map.getZoom();
                    return JSON.stringify({
                        lat: center.lat,
                        lng: center.lng,
                        zoom: zoom
                    });
                }
                return null;
            } catch(e) {
                return null;
            }
        })();
        """
        
        # Use event loop to wait for JavaScript result
        loop = QEventLoop()
        result_holder = {'result': None}
        
        def handle_result(result):
            result_holder['result'] = result
            loop.quit()
        
        # Execute JavaScript
        self.map_view.page().runJavaScript(js_code, handle_result)
        
        # Wait for result (max 200ms timeout)
        QTimer.singleShot(200, loop.quit)
        loop.exec_()
        
        # Parse result and update view settings
        if result_holder['result']:
            try:
                view_data = json.loads(result_holder['result'])
                self.view_state = {
                    'current_center': [view_data['lat'], view_data['lng']],
                    'current_zoom': int(view_data['zoom'])
                }
            except:
                pass
    
    def take_screenshot(self):
        """Capture a screenshot of the map view"""
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"map_screenshot_{timestamp}.png"
        
        # Ask user where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            default_filename,
            "PNG Images (*.png);;JPEG Images (*.jpg);;All Files (*)"
        )
        
        if file_path:
            # Capture the screenshot
            pixmap = self.map_view.grab()
            
            # Save the screenshot
            if pixmap.save(file_path):
                self.statusBar().showMessage(f"Screenshot saved: {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save screenshot")
