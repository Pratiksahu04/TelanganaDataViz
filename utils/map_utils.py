import folium
import json
import numpy as np
import pandas as pd
from shapely.geometry import shape, Point
import streamlit as st
import math

class MapUtils:
    def __init__(self, geojson_data):
        self.geojson_data = geojson_data
        self.center_lat = 18.1124
        self.center_lng = 79.0193
        self.zoom_start = 7
    
    def create_basic_map(self):
        """
        Create a basic map with district boundaries
        """
        m = folium.Map(
            location=[self.center_lat, self.center_lng],
            zoom_start=self.zoom_start,
            tiles='CartoDB positron' # Professional looking base map
        )
        
        # Add district boundaries
        folium.GeoJson(
            self.geojson_data,
            style_function=lambda feature: {
                'fillColor': '#e0f2f7', # Light blue for uncolored districts
                'color': '#333',
                'weight': 1,
                'fillOpacity': 0.7,
            },
            tooltip=folium.features.GeoJsonTooltip(
                fields=['district'],
                aliases=['District:'],
                labels=True,
                sticky=True, # Make tooltip stick to cursor
                style="""
                    background-color: #F8F9FA;
                    color: #333;
                    border: 1px solid #AAA;
                    border-radius: 4px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    padding: 8px;
                """,
                max_width=300
            ),
            highlight_function=lambda x: { # Subtle highlight on hover
                'fillColor': '#a7d9ed',
                'color':'#007bff',
                'weight':2,
                'fillOpacity':0.7
            }
        ).add_to(m)
        
        return m
    
    def create_choropleth_map(self, data, metric_col, color_scheme='viridis'):
        """
        Create a choropleth map colored by the specified metric, with hover data.
        """
        # Create base map
        m = folium.Map(
            location=[self.center_lat, self.center_lng],
            zoom_start=self.zoom_start,
            tiles='CartoDB positron'
        )
        
        # Prepare data for choropleth
        district_col = None
        for col in data.columns:
            if data[col].dtype == 'object':
                sample_values = data[col].dropna().unique()[:5]
                geojson_districts = [f['properties']['district'] for f in self.geojson_data['features']]
                
                matches = sum(1 for val in sample_values if val in geojson_districts)
                if matches > 0:
                    district_col = col
                    break
        
        if district_col is None:
            st.error("Could not identify district column for mapping")
            return self.create_basic_map()
        
        # Create a dictionary mapping district names to metric values for coloring
        district_values = dict(zip(data[district_col], data[metric_col]))
        
        # Get min and max values for color scaling
        min_val = data[metric_col].min()
        max_val = data[metric_col].max()
        
        # Color function
        def get_color(value):
            if pd.isna(value):
                return '#A9A9A9' # Darker gray for missing data
            
            # Normalize value to 0-1 range
            normalized = (value - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            
            # Define professional color maps (e.g., from ColorBrewer or Matplotlib plasma/viridis/etc.)
            # Using a custom professional palette for better control
            color_maps = {
                'viridis': ['#440154', '#472C7B', '#3E4989', '#31688E', '#26828E', '#1F9E89', '#35B779', '#6ECE58', '#B5DE2B', '#FDE725'],
                'plasma': ['#0D0887', '#46039F', '#7201A8', '#9C179E', '#BD3786', '#D8576B', '#ED7953', '#FB9F3A', '#FDCA26', '#F0F921'],
                'inferno': ['#000004', '#1B0C41', '#4A0C6B', '#781C6D', '#A52C60', '#CF4446', '#ED6925', '#FB9B06', '#F7D03C', '#FCFFA4'],
                'magma': ['#000004', '#180F3D', '#440F76', '#721F81', '#9E2F7F', '#CD4071', '#F1605D', '#FD9668', '#FECA8D', '#FCFDBF'],
                'cividis': ['#00224E', '#123570', '#3B496C', '#575D6D', '#707173', '#8A8678', '#A59C74', '#C3B369', '#E1CC55', '#FEE838'],
                'Blues': ['#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'], # Less saturated
                'Reds': ['#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#a50f15', '#67000d'], # Less saturated
                'Greens': ['#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#006d2c', '#00441b'] # Less saturated
            }
            
            colors = color_maps.get(color_scheme, color_maps['viridis'])
            color_idx = int(normalized * (len(colors) - 1))
            return colors[color_idx]
        
        # Create a deep copy of the geojson data to add metric_col to properties
        geojson_data_with_metrics = json.loads(json.dumps(self.geojson_data)) # Deep copy

        for feature in geojson_data_with_metrics['features']:
            district_name = feature['properties']['district']
            # Get the corresponding row from the input data DataFrame
            row = data[data[district_col] == district_name]
            if not row.empty:
                value_to_add = row[metric_col].iloc[0]
                # Convert NumPy numeric types to standard Python float or int, handle NaN
                if pd.isna(value_to_add):
                    feature['properties'][metric_col] = None # JSON null for NaN
                else:
                    feature['properties'][metric_col] = float(value_to_add) # Convert to Python float
            else:
                # Handle cases where a district in geojson has no matching data
                feature['properties'][metric_col] = None 

        # Style function now also relies on metric_col being in feature.properties
        def style_function(feature):
            # Access value from properties (where we just added it)
            value = feature['properties'].get(metric_col, None) 
            
            return {
                'fillColor': get_color(value),
                'color': '#333', # Darker border
                'weight': 1, # Thinner border
                'fillOpacity': 0.8, # Slightly higher opacity for choropleth
            }
        
        # Add choropleth layer using the modified geojson_data_with_metrics
        folium.GeoJson(
            geojson_data_with_metrics, # Use the modified GeoJSON data
            style_function=style_function,
            tooltip=folium.features.GeoJsonTooltip(
                fields=['district', metric_col], # These fields are now available in feature.properties
                aliases=['District:', f'{metric_col}:'], # Descriptive aliases for display
                labels=True,
                sticky=True, # Make tooltip stick to cursor
                fmt=".2f", # Format numbers to 2 decimal places in tooltip
                style="""
                    background-color: #F8F9FA;
                    color: #333;
                    border: 1px solid #AAA;
                    border-radius: 4px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    padding: 8px;
                """,
                max_width=300
            ),
            highlight_function=lambda x: { # Add highlight for better user experience on hover
                'fillColor': '#FFFFB3', # Lighter yellow for highlight
                'color':'#007bff', # Blue border for highlight
                'weight':2, # Slightly thicker border on hover
                'dashArray':'', # Solid line on hover
                'fillOpacity':0.8
            }
        ).add_to(m)
        
        # Add a custom legend
        self._add_legend(m, min_val, max_val, color_scheme, metric_col)
        
        return m
    
    def _add_legend(self, map_obj, min_val, max_val, color_scheme, metric_name):
        """
        Add a color legend to the map with improved styling.
        """
        # Define the number of steps for the legend gradient
        n_steps = 10 
        
        # Get the colors from the selected color scheme
        color_maps = {
            'viridis': ['#440154', '#472C7B', '#3E4989', '#31688E', '#26828E', '#1F9E89', '#35B779', '#6ECE58', '#B5DE2B', '#FDE725'],
            'plasma': ['#0D0887', '#46039F', '#7201A8', '#9C179E', '#BD3786', '#D8576B', '#ED7953', '#FB9F3A', '#FDCA26', '#F0F921'],
            'inferno': ['#000004', '#1B0C41', '#4A0C6B', '#781C6D', '#A52C60', '#CF4446', '#ED6925', '#FB9B06', '#F7D03C', '#FCFFA4'],
            'magma': ['#000004', '#180F3D', '#440F76', '#721F81', '#9E2F7F', '#CD4071', '#F1605D', '#FD9668', '#FECA8D', '#FCFDBF'],
            'cividis': ['#00224E', '#123570', '#3B496C', '#575D6D', '#707173', '#8A8678', '#A59C74', '#C3B369', '#E1CC55', '#FEE838'],
            'Blues': ['#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'], 
            'Reds': ['#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#a50f15', '#67000d'],
            'Greens': ['#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#006d2c', '#00441b']
        }
        colors = color_maps.get(color_scheme, color_maps['viridis'])

        # Create gradient for legend
        gradient_stops = ""
        for i, color in enumerate(colors):
            position = (i / (len(colors) - 1)) * 100
            gradient_stops += f"{color} {position}%"
            if i < len(colors) - 1:
                gradient_stops += ", "

        # Legend HTML
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 180px; height: 120px; 
                    background-color: Black; 
                    border:2px solid #ccc; border-radius: 8px; 
                    box-shadow: 3px 3px 10px rgba(0,0,0,0.2);
                    z-index:9999; 
                    font-size:12px; padding: 12px; font-family: Arial, sans-serif;">
            <h4 style="margin-top:0; margin-bottom: 8px; font-weight: bold;">{metric_name}</h4>
            <div style="width: 100%; height: 20px; 
                        background: linear-gradient(to right, {gradient_stops}); 
                        border-radius: 3px; margin-bottom: 5px;"></div>
            <div style="display: flex; justify-content: space-between;">
                <span>{min_val:.2f}</span>
                <span>{max_val:.2f}</span>
            </div>
            <p style="margin-top: 5px; font-style: italic; color: #060606;">(Missing data: Gray)</p>
        </div>
        '''
        
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def get_district_from_coordinates(self, lat, lng, geojson_data):
        """
        Get district name from clicked coordinates
        """
        point = Point(lng, lat)
        
        for feature in geojson_data['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                return feature['properties']['district']
        
        return None
    
    def get_district_bounds(self, district_name):
        """
        Get the bounding box for a specific district
        """
        for feature in self.geojson_data['features']:
            if feature['properties']['district'] == district_name:
                coords = feature['geometry']['coordinates'][0] # Assuming single polygon per district
                
                # Check for MultiPolygon case
                if feature['geometry']['type'] == 'MultiPolygon':
                    all_lats = []
                    all_lngs = []
                    for poly_coords in feature['geometry']['coordinates']:
                        for ring in poly_coords: # A list of rings, usually just one exterior ring
                            all_lats.extend([coord[1] for coord in ring])
                            all_lngs.extend([coord[0] for coord in ring])
                    if all_lats and all_lngs:
                        return {
                            'min_lat': min(all_lats),
                            'max_lat': max(all_lats),
                            'min_lng': min(all_lngs),
                            'max_lng': max(all_lngs)
                        }
                    else:
                        return None # No coordinates found in MultiPolygon
                else: # Polygon case
                    lats = [coord[1] for coord in coords]
                    lngs = [coord[0] for coord in coords]
                    return {
                        'min_lat': min(lats),
                        'max_lat': max(lats),
                        'min_lng': min(lngs),
                        'max_lng': max(lngs)
                    }
        return None
    
    def create_focused_map(self, district_name, data=None, metric_col=None):
        """
        Create a map focused on a specific district
        """
        bounds = self.get_district_bounds(district_name)
        if not bounds:
            return self.create_basic_map()
        
        center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
        center_lng = (bounds['min_lng'] + bounds['max_lng']) / 2
        
        # Adjust zoom level for a single district. Higher zoom for smaller districts.
        # This is a heuristic and might need fine-tuning.
        lat_diff = bounds['max_lat'] - bounds['min_lat']
        lng_diff = bounds['max_lng'] - bounds['min_lng']
        max_diff = max(lat_diff, lng_diff)
        
        if max_diff < 0.1: # Very small district
            zoom = 12
        elif max_diff < 0.3:
            zoom = 10
        elif max_diff < 0.6:
            zoom = 9
        else:
            zoom = 8 # Larger districts
            
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom,
            tiles='CartoDB positron'
        )
        
        # Add the specific district with highlighting
        for feature in self.geojson_data['features']:
            if feature['properties']['district'] == district_name:
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': '#007bff', # A professional blue for selection
                        'color': '#0056b3', # Darker blue border
                        'weight': 2,
                        'fillOpacity': 0.7,
                    },
                    tooltip=folium.features.GeoJsonTooltip(
                        fields=['district'],
                        aliases=['District:'],
                        labels=True,
                        sticky=True,
                        style="""
                            background-color: #F8F9FA;
                            color: #333;
                            border: 1px solid #AAA;
                            border-radius: 4px;
                            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                            font-family: Arial, sans-serif;
                            font-size: 12px;
                            padding: 8px;
                        """,
                        max_width=300
                    )
                ).add_to(m)
            else:
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': '#e9ecef', # Very light gray for other districts
                        'color': '#adb5bd', # Light gray border
                        'weight': 1,
                        'fillOpacity': 0.5,
                    }
                ).add_to(m)
        
        return m
    
    def calculate_distance_between_districts(self, district1, district2):
        """
        Calculate the distance between two districts in kilometers
        """
        coords1 = self.get_district_centroid(district1)
        coords2 = self.get_district_centroid(district2)
        
        if coords1 is None or coords2 is None:
            return None
        
        return self.haversine_distance(coords1[0], coords1[1], coords2[0], coords2[1])
    
    def get_district_centroid(self, district_name):
        """
        Get the centroid coordinates (lat, lng) for a district
        """
        for feature in self.geojson_data['features']:
            if feature['properties']['district'] == district_name:
                polygon = shape(feature['geometry'])
                centroid = polygon.centroid
                return (centroid.y, centroid.x)  # (lat, lng)
        return None
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points on the earth in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def create_distance_map(self, district1, district2):
        """
        Create a map showing the distance between two districts
        """
        coords1 = self.get_district_centroid(district1)
        coords2 = self.get_district_centroid(district2)
        
        if coords1 is None or coords2 is None:
            return self.create_basic_map()
        
        # Calculate center point between the two districts
        center_lat = (coords1[0] + coords2[0]) / 2
        center_lng = (coords1[1] + coords2[1]) / 2
        
        # Calculate appropriate zoom level based on distance
        distance = self.haversine_distance(coords1[0], coords1[1], coords2[0], coords2[1])
        if distance < 50:
            zoom = 10
        elif distance < 100:
            zoom = 9
        elif distance < 200:
            zoom = 8
        else:
            zoom = 7 # Adjust as needed
        
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom,
            tiles='CartoDB positron'
        )
        
        # Add all districts in light gray
        for feature in self.geojson_data['features']:
            district_name = feature['properties']['district']
            
            if district_name == district1:
                # Highlight first district in a distinct color
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': '#28a745', # Green for 'from'
                        'color': '#218838',
                        'weight': 2,
                        'fillOpacity': 0.7,
                    },
                    tooltip=folium.features.GeoJsonTooltip(
                        fields=['district'],
                        aliases=['District:'],
                        labels=True,
                        sticky=True,
                        style="""
                            background-color: #F8F9FA;
                            color: #333;
                            border: 1px solid #AAA;
                            border-radius: 4px;
                            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                            font-family: Arial, sans-serif;
                            font-size: 12px;
                            padding: 8px;
                        """,
                        max_width=300
                    )
                ).add_to(m)
            elif district_name == district2:
                # Highlight second district in another distinct color
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': '#dc3545', # Red for 'to'
                        'color': '#c82333',
                        'weight': 2,
                        'fillOpacity': 0.7,
                    },
                    tooltip=folium.features.GeoJsonTooltip(
                        fields=['district'],
                        aliases=['District:'],
                        labels=True,
                        sticky=True,
                        style="""
                            background-color: #F8F9FA;
                            color: #333;
                            border: 1px solid #AAA;
                            border-radius: 4px;
                            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                            font-family: Arial, sans-serif;
                            font-size: 12px;
                            padding: 8px;
                        """,
                        max_width=300
                    )
                ).add_to(m)
            else:
                # Other districts in a subtle light gray
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': '#e9ecef',
                        'color': '#adb5bd',
                        'weight': 1,
                        'fillOpacity': 0.4,
                    }
                ).add_to(m)
        
        # Add markers for district centroids with professional icons
        folium.Marker(
            coords1,
            popup=f"<b>{district1}</b>",
            icon=folium.Icon(color='green', icon='play', prefix='fa') # Play icon for start
        ).add_to(m)
        
        folium.Marker(
            coords2,
            popup=f"<b>{district2}</b>",
            icon=folium.Icon(color='red', icon='stop', prefix='fa') # Stop icon for end
        ).add_to(m)
        
        # Add a line between the districts
        distance_text = f"Distance: {distance:.2f} km"
        folium.PolyLine(
            locations=[coords1, coords2],
            weight=4,
            color='#6f42c1', # Professional purple
            opacity=0.8,
            dash_array='5, 5', # Dashed line
            popup=folium.Popup(distance_text, max_width=150) # Popup for the line
        ).add_to(m)
        
        return m
