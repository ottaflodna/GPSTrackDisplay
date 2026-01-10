"""
Track data model - common structure for GPX and IGC tracks
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class TrackPoint:
    """Single point in a GPS track"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def to_latlng(self):
        """Return as [lat, lng] for mapping libraries"""
        return [self.latitude, self.longitude]


class Track:
    """GPS Track containing multiple points"""
    
    def __init__(self, name: str, track_type: str = "unknown"):
        """
        Initialize a track
        
        Args:
            name: Track name (usually filename)
            track_type: Type of track ('gpx', 'igc')
        """
        self.name = name
        self.track_type = track_type
        self.points: List[TrackPoint] = []
        self.color: Optional[str] = None
    
    def add_point(self, point: TrackPoint):
        """Add a point to the track"""
        self.points.append(point)
    
    def get_bounds(self):
        """Calculate bounding box of the track"""
        if not self.points:
            return None
        
        lats = [p.latitude for p in self.points]
        lngs = [p.longitude for p in self.points]
        
        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lng': min(lngs),
            'max_lng': max(lngs)
        }
    
    def get_center(self):
        """Calculate center point of the track"""
        bounds = self.get_bounds()
        if not bounds:
            return None
        
        center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
        center_lng = (bounds['min_lng'] + bounds['max_lng']) / 2
        return [center_lat, center_lng]
    
    def get_total_distance(self):
        """Calculate total distance in kilometers (simplified)"""
        if len(self.points) < 2:
            return 0.0
        
        from math import radians, cos, sin, asin, sqrt
        
        total = 0.0
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            
            # Haversine formula
            lon1, lat1, lon2, lat2 = map(radians, [p1.longitude, p1.latitude, 
                                                     p2.longitude, p2.latitude])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radius of earth in kilometers
            total += c * r
        
        return total
    
    def __len__(self):
        """Return number of points"""
        return len(self.points)
    
    def __repr__(self):
        return f"Track(name='{self.name}', type='{self.track_type}', points={len(self.points)})"
