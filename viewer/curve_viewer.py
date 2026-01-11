"""
Curve Viewer - Displays track data as interactive charts/curves
Example of reusing the base architecture for a different visualization
"""

import os
from typing import List, Dict, Any, Optional
from models.track import Track
from viewer.base_viewer import BaseViewer


class CurveViewer(BaseViewer):
    """
    Create and display interactive charts with GPS track data
    Shows altitude, speed, power, heart rate, etc. over time/distance
    """
    
    # Available chart types
    AVAILABLE_CHARTS = [
        'Altitude Profile',
        'Speed Profile',
        'Heart Rate Profile',
        'Power Profile',
        'Cadence Profile',
        'Temperature Profile',
        'Multi-View (All)'
    ]
    
    # X-axis options
    X_AXIS_OPTIONS = [
        'Distance (km)',
        'Time',
        'Point Index'
    ]
    
    def get_available_options(self) -> Dict[str, Any]:
        """Get available configuration options for curve viewer"""
        return {
            'chart_type': {
                'type': 'combo',
                'values': self.AVAILABLE_CHARTS,
                'label': 'Chart Type'
            },
            'x_axis': {
                'type': 'combo',
                'values': self.X_AXIS_OPTIONS,
                'label': 'X-Axis'
            },
            'show_grid': {
                'type': 'checkbox',
                'label': 'Show Grid'
            },
            'show_legend': {
                'type': 'checkbox',
                'label': 'Show Legend'
            },
            'smooth_data': {
                'type': 'checkbox',
                'label': 'Smooth Data'
            }
        }
    
    def get_default_options(self) -> Dict[str, Any]:
        """Get default values for all options"""
        return {
            'chart_type': 'Altitude Profile',
            'x_axis': 'Distance (km)',
            'show_grid': True,
            'show_legend': True,
            'smooth_data': False
        }
    
    def create_view(self, tracks: List[Track], output_file: str = 'track_curves.html', **kwargs) -> tuple:
        """
        Create interactive charts with track data
        
        Args:
            tracks: List of Track objects to display
            output_file: Output HTML filename
            **kwargs: Curve-specific options
            
        Returns:
            Tuple of (file_path, view_state_dict)
        """
        if not tracks:
            raise ValueError("No tracks provided")
        
        # Extract options with defaults
        chart_type = kwargs.get('chart_type', 'Altitude Profile')
        x_axis = kwargs.get('x_axis', 'Distance (km)')
        show_grid = kwargs.get('show_grid', True)
        show_legend = kwargs.get('show_legend', True)
        smooth_data = kwargs.get('smooth_data', False)
        
        # Generate HTML with Plotly charts
        html_content = self._generate_html(
            tracks, chart_type, x_axis, show_grid, show_legend, smooth_data
        )
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Return file path and empty view state (curves don't have zoom/pan state like maps)
        view_state = {}
        
        return (os.path.abspath(output_file), view_state)
    
    def _generate_html(self, tracks: List[Track], chart_type: str, x_axis: str,
                      show_grid: bool, show_legend: bool, smooth_data: bool) -> str:
        """Generate HTML with Plotly charts"""
        
        # Start HTML document
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Track Curves</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .chart-container {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-top: 0;
        }
    </style>
</head>
<body>
    <h1>Track Curve Viewer</h1>
"""
        
        if chart_type == 'Multi-View (All)':
            # Show multiple charts
            html += self._create_multi_view_charts(tracks, x_axis, show_grid, show_legend, smooth_data)
        else:
            # Show single chart
            html += self._create_single_chart(tracks, chart_type, x_axis, show_grid, show_legend, smooth_data)
        
        html += """
</body>
</html>
"""
        return html
    
    def _create_single_chart(self, tracks: List[Track], chart_type: str, x_axis: str,
                            show_grid: bool, show_legend: bool, smooth_data: bool) -> str:
        """Create a single chart"""
        # Determine y-axis attribute based on chart type
        y_attr_map = {
            'Altitude Profile': ('altitude', 'Altitude (m)'),
            'Speed Profile': ('speed', 'Speed (km/h)'),
            'Heart Rate Profile': ('heart_rate', 'Heart Rate (bpm)'),
            'Power Profile': ('power', 'Power (W)'),
            'Cadence Profile': ('cadence', 'Cadence (rpm)'),
            'Temperature Profile': ('temperature', 'Temperature (°C)')
        }
        
        y_attr, y_label = y_attr_map.get(chart_type, ('altitude', 'Value'))
        
        chart_id = 'chart1'
        html = f'<div class="chart-container"><div id="{chart_id}"></div></div>\n'
        
        # Generate Plotly data
        html += '<script>\n'
        html += f'var data_{chart_id} = [\n'
        
        for idx, track in enumerate(tracks):
            x_values = self._get_x_values(track, x_axis)
            y_values = self._get_y_values(track, y_attr)
            
            if not x_values or not y_values:
                continue
            
            # Filter out None values
            filtered_data = [(x, y) for x, y in zip(x_values, y_values) if y is not None]
            if not filtered_data:
                continue
            
            x_filtered, y_filtered = zip(*filtered_data)
            
            html += '{\n'
            html += f'  x: {list(x_filtered)},\n'
            html += f'  y: {list(y_filtered)},\n'
            html += f'  name: "{track.name}",\n'
            html += f'  type: "scatter",\n'
            html += f'  mode: "lines",\n'
            html += f'  line: {{{{color: "{track.color or "#1f77b4"}", width: 2}}}}\n'
            html += '}' + (',' if idx < len(tracks) - 1 else '') + '\n'
        
        html += '];\n'
        
        # Layout configuration
        html += f'var layout_{chart_id} = {{{{\n'
        html += f'  title: "{chart_type}",\n'
        html += f'  xaxis: {{{{title: "{x_axis}", showgrid: {str(show_grid).lower()}}}}},\n'
        html += f'  yaxis: {{{{title: "{y_label}", showgrid: {str(show_grid).lower()}}}}},\n'
        html += f'  showlegend: {str(show_legend).lower()},\n'
        html += '  hovermode: "x unified"\n'
        html += '}};\n'
        
        html += f'Plotly.newPlot("{chart_id}", data_{chart_id}, layout_{chart_id});\n'
        html += '</script>\n'
        
        return html
    
    def _create_multi_view_charts(self, tracks: List[Track], x_axis: str,
                                  show_grid: bool, show_legend: bool, smooth_data: bool) -> str:
        """Create multiple charts in a grid layout"""
        chart_configs = [
            ('Altitude Profile', 'altitude', 'Altitude (m)'),
            ('Speed Profile', 'speed', 'Speed (km/h)'),
            ('Heart Rate Profile', 'heart_rate', 'Heart Rate (bpm)'),
            ('Power Profile', 'power', 'Power (W)')
        ]
        
        html = ''
        
        for idx, (title, y_attr, y_label) in enumerate(chart_configs):
            chart_id = f'chart{idx + 1}'
            html += f'<div class="chart-container"><div id="{chart_id}"></div></div>\n'
            
            # Generate Plotly data
            html += '<script>\n'
            html += f'var data_{chart_id} = [\n'
            
            for track_idx, track in enumerate(tracks):
                x_values = self._get_x_values(track, x_axis)
                y_values = self._get_y_values(track, y_attr)
                
                if not x_values or not y_values:
                    continue
                
                # Filter out None values
                filtered_data = [(x, y) for x, y in zip(x_values, y_values) if y is not None]
                if not filtered_data:
                    continue
                
                x_filtered, y_filtered = zip(*filtered_data)
                
                html += '{\n'
                html += f'  x: {list(x_filtered)},\n'
                html += f'  y: {list(y_filtered)},\n'
                html += f'  name: "{track.name}",\n'
                html += f'  type: "scatter",\n'
                html += f'  mode: "lines",\n'
                html += f'  line: {{{{color: "{track.color or "#1f77b4"}", width: 2}}}}\n'
                html += '}' + (',' if track_idx < len(tracks) - 1 else '') + '\n'
            
            html += '];\n'
            
            # Layout configuration
            html += f'var layout_{chart_id} = {{{{\n'
            html += f'  title: "{title}",\n'
            html += f'  xaxis: {{{{title: "{x_axis}", showgrid: {str(show_grid).lower()}}}}},\n'
            html += f'  yaxis: {{{{title: "{y_label}", showgrid: {str(show_grid).lower()}}}}},\n'
            html += f'  showlegend: {str(show_legend).lower()},\n'
            html += '  hovermode: "x unified",\n'
            html += '  height: 350\n'
            html += '}};\n'
            
            html += f'Plotly.newPlot("{chart_id}", data_{chart_id}, layout_{chart_id});\n'
            html += '</script>\n'
        
        return html
    
    def _get_x_values(self, track: Track, x_axis: str) -> List:
        """Get x-axis values based on selection"""
        if x_axis == 'Distance (km)':
            # Calculate cumulative distance
            from math import radians, cos, sin, asin, sqrt
            distances = [0.0]
            for i in range(1, len(track.points)):
                p1 = track.points[i - 1]
                p2 = track.points[i]
                
                lon1, lat1, lon2, lat2 = map(radians, [p1.longitude, p1.latitude, 
                                                         p2.longitude, p2.latitude])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                r = 6371  # Earth radius in km
                distances.append(distances[-1] + c * r)
            return distances
        
        elif x_axis == 'Time':
            # Return timestamps if available
            if track.points and track.points[0].timestamp:
                base_time = track.points[0].timestamp
                return [(p.timestamp - base_time).total_seconds() / 60.0  # minutes
                       for p in track.points if p.timestamp]
            return list(range(len(track.points)))
        
        else:  # Point Index
            return list(range(len(track.points)))
    
    def _get_y_values(self, track: Track, attribute: str) -> List:
        """Get y-axis values based on attribute"""
        return [getattr(p, attribute, None) for p in track.points]
    
    def get_required_track_attributes(self) -> List[str]:
        """Get list of required track point attributes"""
        return ['altitude', 'timestamp']  # Minimum required for curve viewing
