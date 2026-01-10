"""
GPS Tracklog Viewer - Main Entry Point
Supports GPX (bike) and IGC (paragliding) formats
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


def main():
    """Main application entry point"""
    # Required for QtWebEngineWidgets - MUST be set before any imports that use it
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    # Import after setting the attribute
    from ui.main_window import MainWindow
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    # Create and show main window
    window = MainWindow()
    window.showMaximized()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
