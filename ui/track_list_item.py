"""
Reusable track list item widget
Displays track properties with inline editing
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, 
                             QSpinBox, QPushButton)
from PyQt5.QtCore import pyqtSignal
from models.track import Track


class TrackListItem(QWidget):
    """Custom widget for track list item with editable properties"""
    
    properties_changed = pyqtSignal()
    remove_requested = pyqtSignal(object)
    
    def __init__(self, track: Track, parent=None):
        super().__init__(parent)
        self.track = track
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for track item"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Color display (non-clickable)
        self.color_label = QLabel()
        self.color_label.setFixedSize(30, 30)
        self.color_label.setStyleSheet(
            f"background-color: {self.track.color or '#FF0000'}; "
            f"border: 2px solid #666; border-radius: 3px;"
        )
        layout.addWidget(self.color_label)
        
        # Name input
        self.name_input = QLineEdit(self.track.name)
        self.name_input.textChanged.connect(self.update_name)
        layout.addWidget(self.name_input, stretch=3)
        
        # Line width spinner
        width_label = QLabel("Width:")
        layout.addWidget(width_label)
        
        self.width_spinner = QSpinBox()
        self.width_spinner.setMinimum(1)
        self.width_spinner.setMaximum(10)
        self.width_spinner.setValue(getattr(self.track, 'line_width', 5))
        self.width_spinner.editingFinished.connect(self.update_width)
        layout.addWidget(self.width_spinner)
        
        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setStyleSheet(
            "background-color: #ff4444; color: white; font-weight: bold;"
        )
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        layout.addWidget(remove_btn)
        
        self.setLayout(layout)
    
    def update_name(self, name: str):
        """Update track name"""
        self.track.name = name
        self.properties_changed.emit()
    
    def update_width(self):
        """Update line width"""
        self.track.line_width = self.width_spinner.value()
        self.properties_changed.emit()
    
    def update_color_display(self):
        """Update the color display label"""
        self.color_label.setStyleSheet(
            f"background-color: {self.track.color or '#FF0000'}; "
            f"border: 2px solid #666; border-radius: 3px;"
        )
