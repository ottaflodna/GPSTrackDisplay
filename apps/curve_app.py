"""
Curve Application - GPS Track Curve/Chart Viewer
Demonstrates reuse of base components for a different visualization type
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout,
                             QComboBox, QCheckBox, QFileDialog, QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl
from typing import List
import os
from datetime import datetime

from ui.base_window import BaseWindow
from viewer.base_viewer import BaseViewer
from viewer.curve_viewer import CurveViewer
from models.track import Track


class CurveWindow(BaseWindow):
    """Main window for GPS tracklog curve/chart viewer"""
    
    def __init__(self):
        # Initialize curve-specific properties before calling super().__init__()
        self.chart_type = "Altitude Profile"
        self.x_axis = "Distance (km)"
        self.show_grid = True
        self.show_legend = True
        self.smooth_data = False
        
        super().__init__()
        self.setWindowTitle("GPS Tracklog Curve Viewer")
        
        # Add screenshot button to track manager (after it's created)
        from PyQt5.QtWidgets import QPushButton
        screenshot_btn = QPushButton("Screenshot")
        screenshot_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        screenshot_btn.clicked.connect(self.take_screenshot)
        self.track_manager.widget().layout().addWidget(screenshot_btn)
    
    def create_viewer(self) -> BaseViewer:
        """Create and return the curve viewer instance"""
        return CurveViewer()
    
    def setup_viewer_widget(self):
        """Setup the curve display as central widget"""
        central_widget = QWidget()
        curve_layout = QVBoxLayout()
        central_widget.setLayout(curve_layout)
        
        # Web view for charts
        self.curve_view = QWebEngineView()
        curve_layout.addWidget(self.curve_view)
        
        # Set as central widget
        self.setCentralWidget(central_widget)
    
    def setup_viewer_properties_dock(self):
        """Setup the curve properties dock widget"""
        from PyQt5.QtWidgets import QDockWidget
        
        # Create dock widget
        properties_dock = QDockWidget("Curve Properties", self)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        
        # Create properties widget
        properties_widget = QWidget()
        properties_layout = QFormLayout()
        properties_widget.setLayout(properties_layout)
        
        # Chart settings group
        chart_groupbox = QGroupBox("Chart settings")
        chart_layout = QFormLayout()
        chart_groupbox.setLayout(chart_layout)
        properties_layout.addRow(chart_groupbox)
        
        # Chart type selector
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(CurveViewer.AVAILABLE_CHARTS)
        self.chart_type_combo.setCurrentText(self.chart_type)
        self.chart_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        chart_layout.addRow("Chart type:", self.chart_type_combo)
        
        # X-axis selector
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.addItems(CurveViewer.X_AXIS_OPTIONS)
        self.x_axis_combo.setCurrentText(self.x_axis)
        self.x_axis_combo.currentTextChanged.connect(self.on_x_axis_changed)
        chart_layout.addRow("X-axis:", self.x_axis_combo)
        
        # Display settings group
        display_groupbox = QGroupBox("Display settings")
        display_layout = QFormLayout()
        display_groupbox.setLayout(display_layout)
        properties_layout.addRow(display_groupbox)
        
        # Show grid checkbox
        self.show_grid_checkbox = QCheckBox()
        self.show_grid_checkbox.setChecked(self.show_grid)
        self.show_grid_checkbox.stateChanged.connect(self.on_show_grid_changed)
        display_layout.addRow("Show grid:", self.show_grid_checkbox)
        
        # Show legend checkbox
        self.show_legend_checkbox = QCheckBox()
        self.show_legend_checkbox.setChecked(self.show_legend)
        self.show_legend_checkbox.stateChanged.connect(self.on_show_legend_changed)
        display_layout.addRow("Show legend:", self.show_legend_checkbox)
        
        # Smooth data checkbox
        self.smooth_data_checkbox = QCheckBox()
        self.smooth_data_checkbox.setChecked(self.smooth_data)
        self.smooth_data_checkbox.stateChanged.connect(self.on_smooth_data_changed)
        display_layout.addRow("Smooth data:", self.smooth_data_checkbox)
        
        # Set widget to dock
        properties_dock.setWidget(properties_widget)
        
        # Add dock to main window on left side, below tracks dock
        self.addDockWidget(Qt.LeftDockWidgetArea, properties_dock)
        self.splitDockWidget(self.track_manager, properties_dock, Qt.Vertical)
    
    def on_chart_type_changed(self, value: str):
        """Handle chart type selection change"""
        self.chart_type = value
        self.statusBar().showMessage(f"Chart type set to: {value}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_x_axis_changed(self, value: str):
        """Handle X-axis selection change"""
        self.x_axis = value
        self.statusBar().showMessage(f"X-axis set to: {value}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_show_grid_changed(self, state: int):
        """Handle show grid checkbox change"""
        self.show_grid = (state == Qt.Checked)
        self.statusBar().showMessage(f"Grid: {'On' if self.show_grid else 'Off'}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_show_legend_changed(self, state: int):
        """Handle show legend checkbox change"""
        self.show_legend = (state == Qt.Checked)
        self.statusBar().showMessage(f"Legend: {'On' if self.show_legend else 'Off'}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_smooth_data_changed(self, state: int):
        """Handle smooth data checkbox change"""
        self.smooth_data = (state == Qt.Checked)
        self.statusBar().showMessage(f"Data smoothing: {'On' if self.smooth_data else 'Off'}")
        if self.tracks:
            self.on_viewer_properties_changed(fit_bounds=False)
    
    def on_viewer_properties_changed(self, fit_bounds: bool = False):
        """Handle viewer property changes and regenerate curves"""
        self.regenerate_view(fit_bounds)
    
    def get_viewer_options(self) -> dict:
        """Get current viewer options from UI controls"""
        return {
            'chart_type': self.chart_type,
            'x_axis': self.x_axis,
            'show_grid': self.show_grid,
            'show_legend': self.show_legend,
            'smooth_data': self.smooth_data
        }
    
    def load_view_in_widget(self, view_file: str):
        """Load the curve HTML file in the web view"""
        if os.path.exists(view_file):
            url = QUrl.fromLocalFile(os.path.abspath(view_file))
            self.curve_view.setUrl(url)
            self.curve_view.reload()
    
    def initialize_empty_view(self):
        """Initialize an empty view with a message"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Track Curves</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f5f5f5;
        }
        .message {
            text-align: center;
            color: #666;
        }
        h1 {
            color: #333;
        }
    </style>
</head>
<body>
    <div class="message">
        <h1>No Tracks Loaded</h1>
        <p>Use "Add Tracks" to load GPS track files and view their curves.</p>
    </div>
</body>
</html>
"""
        # Save empty view
        view_file = os.path.abspath('track_curves.html')
        with open(view_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.current_view_file = view_file
        self.load_view_in_widget(view_file)
    
    def get_default_output_file(self) -> str:
        """Get default output filename for the curves"""
        return "track_curves.html"
    
    def take_screenshot(self):
        """Capture a screenshot of the curve view"""
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"curves_screenshot_{timestamp}.png"
        
        # Ask user where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            default_filename,
            "PNG Images (*.png);;JPEG Images (*.jpg);;All Files (*)"
        )
        
        if file_path:
            # Capture the screenshot
            pixmap = self.curve_view.grab()
            
            # Save the screenshot
            if pixmap.save(file_path):
                self.statusBar().showMessage(f"Screenshot saved: {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save screenshot")
