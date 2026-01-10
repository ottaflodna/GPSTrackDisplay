"""
Interactive map viewer with ability to add tracks dynamically
"""

import os
import webbrowser
from typing import List
from models.track import Track
from parsers.gpx_parser import GPXParser
from parsers.igc_parser import IGCParser
from ui.file_selector import FileSelector
from viewer.map_viewer import MapViewer


class InteractiveMapViewer:
    """Interactive viewer that allows adding tracks to an open map"""
    
    def __init__(self):
        self.tracks: List[Track] = []
        self.map_viewer = MapViewer()
        self.gpx_parser = GPXParser()
        self.igc_parser = IGCParser()
        self.file_selector = FileSelector()
        self.map_file = 'track_map.html'
    
    def start(self, initial_tracks: List[Track]):
        """
        Start interactive viewer with initial tracks
        
        Args:
            initial_tracks: Initial list of tracks to display
        """
        self.tracks = initial_tracks.copy()
        self._update_map()
        self._open_map()
        self._run_interactive_loop()
    
    def _update_map(self):
        """Regenerate the map with current tracks"""
        if not self.tracks:
            print("No tracks to display")
            return
        
        self.map_viewer.create_map(self.tracks, self.map_file)
        print(f"Map updated with {len(self.tracks)} track(s)")
    
    def _open_map(self):
        """Open the map in default browser"""
        map_path = os.path.abspath(self.map_file)
        webbrowser.open(f'file://{map_path}')
        print(f"Map opened: {map_path}")
    
    def _run_interactive_loop(self):
        """Run interactive command loop"""
        print("\n" + "=" * 50)
        print("Interactive Mode")
        print("=" * 50)
        print("Commands:")
        print("  'a' or 'add'    - Add more tracks")
        print("  'r' or 'reload' - Reload map in browser")
        print("  'q' or 'quit'   - Exit")
        print("=" * 50)
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command in ['q', 'quit', 'exit']:
                    print("Exiting...")
                    break
                
                elif command in ['a', 'add']:
                    self._add_tracks()
                
                elif command in ['r', 'reload']:
                    self._open_map()
                
                else:
                    print(f"Unknown command: '{command}'")
                    print("Use 'a' to add tracks, 'r' to reload, or 'q' to quit")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _add_tracks(self):
        """Add new tracks interactively"""
        print("\nSelect additional track files...")
        file_paths = self.file_selector.select_files()
        
        if not file_paths:
            print("No files selected")
            return
        
        print(f"\nSelected {len(file_paths)} file(s)")
        new_tracks = []
        
        for file_path in file_paths:
            print(f"Parsing: {file_path}")
            try:
                if file_path.lower().endswith('.gpx'):
                    track = self.gpx_parser.parse(file_path)
                elif file_path.lower().endswith('.igc'):
                    track = self.igc_parser.parse(file_path)
                else:
                    print(f"  ⚠ Unsupported file format: {file_path}")
                    continue
                
                if track:
                    new_tracks.append(track)
                    print(f"  ✓ Loaded {len(track.points)} points")
            except Exception as e:
                print(f"  ✗ Error parsing {file_path}: {e}")
        
        if new_tracks:
            self.tracks.extend(new_tracks)
            self._update_map()
            self._open_map()
            print(f"\nAdded {len(new_tracks)} new track(s)")
            print(f"Total tracks: {len(self.tracks)}")
        else:
            print("No tracks loaded successfully")
