"""
IGC file parser for paragliding tracks
"""

import os
from datetime import datetime, date
from models.track import Track, TrackPoint


class IGCParser:
    """Parser for IGC format files (paragliding)"""
    
    def parse(self, file_path: str) -> Track:
        """
        Parse an IGC file and return a Track object
        
        Args:
            file_path: Path to the IGC file
            
        Returns:
            Track object containing parsed data
        """
        track_name = os.path.basename(file_path)
        track = Track(name=track_name, track_type='igc')
        
        flight_date = None
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                # HFDTE record contains the date
                if line.startswith('HFDTE') or line.startswith('HFDTEDATE:'):
                    flight_date = self._parse_date(line)
                
                # B record contains position fixes
                elif line.startswith('B'):
                    point = self._parse_b_record(line, flight_date)
                    if point:
                        track.add_point(point)
        
        return track
    
    def _parse_date(self, line: str) -> date:
        """Parse date from HFDTE record"""
        # Format: HFDTEDDMMYYor HFDTEDDMMYY
        # Example: HFDTE040120 or HFDTEDATE:040120
        date_str = line.replace('HFDTE', '').replace('DATE:', '').strip()
        
        if len(date_str) >= 6:
            day = int(date_str[0:2])
            month = int(date_str[2:4])
            year = int(date_str[4:6])
            
            # Handle 2-digit year (assume 2000s)
            if year < 50:
                year += 2000
            else:
                year += 1900
            
            return date(year, month, day)
        
        return None
    
    def _parse_b_record(self, line: str, flight_date: date = None) -> TrackPoint:
        """
        Parse B record (position fix)
        Format: B HHMMSS DDMMmmmN/S DDDMMmmmE/W A PPPPP GGGGG
        Example: B1602055107126N00249343WA0028000287
        """
        try:
            if len(line) < 35:
                return None
            
            # Time: HHMMSS
            time_str = line[1:7]
            hours = int(time_str[0:2])
            minutes = int(time_str[2:4])
            seconds = int(time_str[4:6])
            
            # Latitude: DDMMmmm N/S
            lat_deg = int(line[7:9])
            lat_min = int(line[9:11])
            lat_min_dec = int(line[11:14])
            lat_dir = line[14]
            
            latitude = lat_deg + (lat_min + lat_min_dec / 1000.0) / 60.0
            if lat_dir == 'S':
                latitude = -latitude
            
            # Longitude: DDDMMmmm E/W
            lon_deg = int(line[15:18])
            lon_min = int(line[18:20])
            lon_min_dec = int(line[20:23])
            lon_dir = line[23]
            
            longitude = lon_deg + (lon_min + lon_min_dec / 1000.0) / 60.0
            if lon_dir == 'W':
                longitude = -longitude
            
            # Altitude: GGGGG (GPS altitude)
            gps_alt = int(line[30:35])
            
            # Create timestamp if we have the date
            timestamp = None
            if flight_date:
                timestamp = datetime.combine(flight_date, 
                                            datetime.min.time().replace(
                                                hour=hours, 
                                                minute=minutes, 
                                                second=seconds))
            
            return TrackPoint(
                latitude=latitude,
                longitude=longitude,
                altitude=gps_alt,
                timestamp=timestamp
            )
        
        except (ValueError, IndexError):
            return None
