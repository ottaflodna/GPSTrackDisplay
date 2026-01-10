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
    
    # IGC-specific fields
    pressure_altitude: Optional[float] = None
    
    # Calculated fields (available for both IGC and GPX)
    vertical_speed_ms: Optional[float] = None  # m/s, calculated from altitude changes
    vertical_speed_mh: Optional[float] = None  # m/h, calculated from altitude changes
    
    # GPX-specific fields (from extensions)
    power: Optional[float] = None  # watts
    heart_rate: Optional[int] = None  # bpm
    cadence: Optional[int] = None  # rpm
    temperature: Optional[float] = None  # celsius
    speed: Optional[float] = None  # m/s
    
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
    
    def calculate_speed(self):
        """Calculate speed for points that don't have it, using Haversine formula"""
        if len(self.points) < 2:
            return
        
        from math import radians, cos, sin, asin, sqrt
        
        # Check if any points need speed calculation
        needs_calculation = any(p.speed is None and p.timestamp is not None 
                               for p in self.points)
        
        if not needs_calculation:
            return
        
        # Calculate speed between consecutive points
        for i in range(1, len(self.points)):
            p1 = self.points[i - 1]
            p2 = self.points[i]
            
            # Only calculate if speed is missing and we have timestamps
            if p2.speed is None and p1.timestamp is not None and p2.timestamp is not None:
                # Calculate time difference in seconds
                time_diff = (p2.timestamp - p1.timestamp).total_seconds()
                
                if time_diff > 0:
                    # Haversine formula for distance
                    lon1, lat1, lon2, lat2 = map(radians, [p1.longitude, p1.latitude, 
                                                             p2.longitude, p2.latitude])
                    dlon = lon2 - lon1
                    dlat = lat2 - lat1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    r = 6371000  # Radius of earth in meters
                    distance = c * r
                    
                    # Speed in m/s, then convert to km/h
                    speed_ms = distance / time_diff
                    p2.speed = speed_ms * 3.6  # Convert to km/h
        
        # Set first point's speed to second point's speed if available
        if self.points[0].speed is None and len(self.points) > 1 and self.points[1].speed is not None:
            self.points[0].speed = self.points[1].speed
    
    def apply_window_averaging(self):
        """Apply window averaging to vertical speed field only"""
        if len(self.points) < 2:
            return
        
        # Average vertical speed over 15 seconds
        self._average_vertical_speed(window_seconds=15)
    
    def _average_power(self, window_seconds: float):
        """Average power values over a time window using efficient sliding window"""
        if not self.points or not any(p.power is not None and p.timestamp is not None for p in self.points):
            return
        
        # Store original values
        original_powers = [p.power for p in self.points]
        half_window = window_seconds / 2
        
        for i, point in enumerate(self.points):
            if point.power is None or point.timestamp is None:
                continue
            
            # Find window boundaries using binary search-like approach
            window_sum = 0.0
            window_count = 0
            
            # Search backward from current point
            for j in range(i, -1, -1):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_powers[j] is not None:
                    window_sum += original_powers[j]
                    window_count += 1
            
            # Search forward from current point (skip current point to avoid double counting)
            for j in range(i + 1, len(self.points)):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_powers[j] is not None:
                    window_sum += original_powers[j]
                    window_count += 1
            
            # Calculate average
            if window_count > 0:
                point.power = window_sum / window_count
    
    def _average_vertical_speed(self, window_seconds: float):
        """Average vertical speed values over a time window using efficient sliding window"""
        if not self.points or not any(p.vertical_speed_mh is not None and p.timestamp is not None for p in self.points):
            return
        
        # Store original values
        original_vspeeds = [p.vertical_speed_mh for p in self.points]
        half_window = window_seconds / 2
        
        for i, point in enumerate(self.points):
            if point.vertical_speed_mh is None or point.timestamp is None:
                continue
            
            # Find window boundaries
            window_sum = 0.0
            window_count = 0
            
            # Search backward from current point
            for j in range(i, -1, -1):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_vspeeds[j] is not None:
                    window_sum += original_vspeeds[j]
                    window_count += 1
            
            # Search forward from current point
            for j in range(i + 1, len(self.points)):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_vspeeds[j] is not None:
                    window_sum += original_vspeeds[j]
                    window_count += 1
            
            # Calculate average
            if window_count > 0:
                point.vertical_speed_mh = window_sum / window_count
                # Also update m/s value
                point.vertical_speed_ms = point.vertical_speed_mh / 3600
    
    def _average_speed(self, window_seconds: float):
        """Average speed values over a time window using efficient sliding window"""
        if not self.points or not any(p.speed is not None and p.timestamp is not None for p in self.points):
            return
        
        # Store original values
        original_speeds = [p.speed for p in self.points]
        half_window = window_seconds / 2
        
        for i, point in enumerate(self.points):
            if point.speed is None or point.timestamp is None:
                continue
            
            # Find window boundaries
            window_sum = 0.0
            window_count = 0
            
            # Search backward from current point
            for j in range(i, -1, -1):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_speeds[j] is not None:
                    window_sum += original_speeds[j]
                    window_count += 1
            
            # Search forward from current point
            for j in range(i + 1, len(self.points)):
                other = self.points[j]
                if other.timestamp is None:
                    continue
                time_diff = abs((point.timestamp - other.timestamp).total_seconds())
                if time_diff > half_window:
                    break
                if original_speeds[j] is not None:
                    window_sum += original_speeds[j]
                    window_count += 1
            
            # Calculate average
            if window_count > 0:
                point.speed = window_sum / window_count
    
    def __len__(self):
        """Return number of points"""
        return len(self.points)
    
    def __repr__(self):
        return f"Track(name='{self.name}', type='{self.track_type}', points={len(self.points)})"
