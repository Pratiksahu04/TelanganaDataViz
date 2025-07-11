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
            tiles='CartoDB positron'
        )
        
        # Add district boundaries
        folium.GeoJson(
            self.geojson_data,
            style_function=lambda feature: {
                'fillColor': '#lightblue',
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0.5,
            },
            tooltip=folium.features.GeoJsonTooltip(
                fields=['district'],
                aliases=['District:'],
                labels=True,
                sticky=False
            )
        ).add_to(m)
        
        return m
    
    def create_choropleth_map(self, data, metric_col, color_scheme='viridis'):
        """
        Create a choropleth map colored by the specified metric
        """
        # Create base map
        m = folium.Map(
            location=[self.center_lat, self.center_lng],
            zoom_start=self.zoom_start,
            tiles='CartoDB positron'
        )
        
        # Prepare data for choropleth
        # Get the district column name (assuming it's the one that matches with GeoJSON)
        district_col = None
        for col in data.columns:
            if data[col].dtype == 'object':
                # Check if this column contains district names that match our GeoJSON
                sample_values = data[col].dropna().unique()[:5]
                geojson_districts = [f['properties']['district'] for f in self.geojson_data['features']]
                
                matches = sum(1 for val in sample_values if val in geojson_districts)
                if matches > 0:
                    district_col = col
                    break
        
        if district_col is None:
            st.error("Could not identify district column for mapping")
            return self.create_basic_map()
        
        # Create a dictionary mapping district names to metric values
        district_values = dict(zip(data[district_col], data[metric_col]))
        
        # Get min and max values for color scaling
        min_val = data[metric_col].min()
        max_val = data[metric_col].max()
        
        # Color function
        def get_color(value):
            if pd.isna(value):
                return '#gray'
            
            # Normalize value to 0-1 range
            normalized = (value - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            
            # Color schemes
            color_maps = {
                'viridis': ['#440154', '#482878', '#3e4989', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6ece58', '#b5de2b', '#fde725'],
                'plasma': ['#0d0887', '#46039f', '#7201a8', '#9c179e', '#bd3786', '#d8576b', '#ed7953', '#fb9f3a', '#fdca26', '#f0f921'],
                'inferno': ['#000004', '#1b0c41', '#4a0c6b', '#781c6d', '#a52c60', '#cf4446', '#ed6925', '#fb9b06', '#f7d03c', '#fcffa4'],
                'magma': ['#000004', '#180f3d', '#440f76', '#721f81', '#9e2f7f', '#cd4071', '#f1605d', '#fd9668', '#feca8d', '#fcfdbf'],
                'cividis': ['#00224e', '#123570', '#3b496c', '#575d6d', '#707173', '#8a8678', '#a59c74', '#c3b369', '#e1cc55', '#fee838'],
                'Blues': ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'],
                'Reds': ['#fff5f0', '#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#a50f15', '#67000d'],
                'Greens': ['#f7fcf5', '#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#006d2c', '#00441b']
            }
            
            colors = color_maps.get(color_scheme, color_maps['viridis'])
            color_idx = int(normalized * (len(colors) - 1))
            return colors[color_idx]
        
        # Style function for GeoJson
        def style_function(feature):
            district_name = feature['properties']['district']
            value = district_values.get(district_name, None)
            
            return {
                'fillColor': get_color(value),
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0.7,
            }
        
        # Add choropleth layer
        folium.GeoJson(
            self.geojson_data,
            style_function=style_function,
            tooltip=folium.features.GeoJsonTooltip(
                fields=['district'],
                aliases=['District:'],
                labels=True,
                sticky=False
            )
        ).add_to(m)
        
        # Add a custom legend
        self._add_legend(m, min_val, max_val, color_scheme, metric_col)
        
        return m
    
    def _add_legend(self, map_obj, min_val, max_val, color_scheme, metric_name):
        """
        Add a color legend to the map
        """
        # Create legend HTML
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><strong>{metric_name}</strong></p>
        <p>Min: {min_val:.2f}</p>
        <p>Max: {max_val:.2f}</p>
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
                coords = feature['geometry']['coordinates'][0]
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
        
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=9,
            tiles='CartoDB positron'
        )
        
        # Add the specific district with highlighting
        for feature in self.geojson_data['features']:
            if feature['properties']['district'] == district_name:
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': 'red',
                        'color': 'darkred',
                        'weight': 3,
                        'fillOpacity': 0.7,
                    },
                    tooltip=folium.features.GeoJsonTooltip(
                        fields=['district'],
                        aliases=['District:'],
                        labels=True,
                        sticky=False
                    )
                ).add_to(m)
            else:
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': 'lightgray',
                        'color': 'gray',
                        'weight': 1,
                        'fillOpacity': 0.3,
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
            zoom = 9
        elif distance < 100:
            zoom = 8
        elif distance < 200:
            zoom = 7
        else:
            zoom = 6
        
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom,
            tiles='CartoDB positron'
        )
        
        # Add all districts in light gray
        for feature in self.geojson_data['features']:
            district_name = feature['properties']['district']
            
            if district_name == district1:
                # Highlight first district in blue
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': 'blue',
                        'color': 'darkblue',
                        'weight': 3,
                        'fillOpacity': 0.7,
                    },
                    tooltip=folium.features.GeoJsonTooltip(
                        fields=['district'],
                        aliases=['District:'],
                        labels=True,
                        sticky=False
                    )
                ).add_to(m)
            elif district_name == district2:
                # Highlight second district in red
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': 'red',
                        'color': 'darkred',
                        'weight': 3,
                        'fillOpacity': 0.7,
                    },
                    tooltip=folium.features.GeoJsonTooltip(
                        fields=['district'],
                        aliases=['District:'],
                        labels=True,
                        sticky=False
                    )
                ).add_to(m)
            else:
                # Other districts in light gray
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': 'lightgray',
                        'color': 'gray',
                        'weight': 1,
                        'fillOpacity': 0.3,
                    }
                ).add_to(m)
        
        # Add markers for district centroids
        folium.Marker(
            coords1,
            popup=f"{district1}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
        
        folium.Marker(
            coords2,
            popup=f"{district2}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Add a line between the districts
        folium.PolyLine(
            locations=[coords1, coords2],
            weight=3,
            color='purple',
            opacity=0.8,
            popup=f"Distance: {distance:.2f} km"
        ).add_to(m)
        
        return m
