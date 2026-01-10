"""
GPX file parser for bike tracks
"""

import gpxpy
import os
from models.track import Track, TrackPoint


class GPXParser:
    """Parser for GPX format files"""
    
    def parse(self, file_path: str) -> Track:
        """
        Parse a GPX file and return a Track object
        
        Args:
            file_path: Path to the GPX file
            
        Returns:
            Track object containing parsed data
        """
        with open(file_path, 'r', encoding='utf-8') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
        
        # Use filename as track name
        track_name = os.path.basename(file_path)
        track = Track(name=track_name, track_type='gpx')
        
        # Extract points from all tracks and segments
        for gpx_track in gpx.tracks:
            for segment in gpx_track.segments:
                for point in segment.points:
                    track_point = TrackPoint(
                        latitude=point.latitude,
                        longitude=point.longitude,
                        altitude=point.elevation,
                        timestamp=point.time
                    )
                    track.add_point(track_point)
        
        # If no tracks, try routes
        if len(track) == 0:
            for route in gpx.routes:
                for point in route.points:
                    track_point = TrackPoint(
                        latitude=point.latitude,
                        longitude=point.longitude,
                        altitude=point.elevation,
                        timestamp=point.time
                    )
                    track.add_point(track_point)
        
        # If still no points, try waypoints
        if len(track) == 0:
            for point in gpx.waypoints:
                track_point = TrackPoint(
                    latitude=point.latitude,
                    longitude=point.longitude,
                    altitude=point.elevation,
                    timestamp=point.time
                )
                track.add_point(track_point)
        
        return track
