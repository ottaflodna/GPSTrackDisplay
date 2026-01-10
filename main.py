"""
GPS Tracklog Viewer - Main Entry Point
Supports GPX (bike) and IGC (paragliding) formats
"""

from ui.file_selector import FileSelector
from parsers.gpx_parser import GPXParser
from parsers.igc_parser import IGCParser
from viewer.map_viewer import MapViewer
from viewer.interactive_viewer import InteractiveMapViewer


def main():
    """Main application entry point"""
    print("GPS Tracklog Viewer")
    print("=" * 50)
    
    # Step 1: Select files
    selector = FileSelector()
    file_paths = selector.select_files()
    
    if not file_paths:
        print("No files selected. Exiting.")
        return
    
    print(f"\nSelected {len(file_paths)} file(s)")
    
    # Step 2: Parse files
    tracks = []
    gpx_parser = GPXParser()
    igc_parser = IGCParser()
    
    for file_path in file_paths:
        print(f"Parsing: {file_path}")
        try:
            if file_path.lower().endswith('.gpx'):
                track = gpx_parser.parse(file_path)
            elif file_path.lower().endswith('.igc'):
                track = igc_parser.parse(file_path)
            else:
                print(f"  ⚠ Unsupported file format: {file_path}")
                continue
            
            if track:
                tracks.append(track)
                print(f"  ✓ Loaded {len(track.points)} points")
        except Exception as e:
            print(f"  ✗ Error parsing {file_path}: {e}")
    
    if not tracks:
        print("\nNo tracks loaded successfully. Exiting.")
        return
    
    # Step 3: Start interactive viewer
    print(f"\nGenerating map with {len(tracks)} track(s)...")
    interactive_viewer = InteractiveMapViewer()
    interactive_viewer.start(tracks)


if __name__ == "__main__":
    main()
