import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
from utils.data_processor import DataProcessor
from utils.map_utils import MapUtils
from utils.chart_utils import ChartUtils

# Page configuration
st.set_page_config(
    page_title="Telangana District Analysis",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'selected_district' not in st.session_state:
    st.session_state.selected_district = None
if 'map_data' not in st.session_state:
    st.session_state.map_data = None
if 'show_distance_map' not in st.session_state:
    st.session_state.show_distance_map = False
if 'distance_from' not in st.session_state:
    st.session_state.distance_from = None
if 'distance_to' not in st.session_state:
    st.session_state.distance_to = None

# Load GeoJSON data
@st.cache_data
def load_geojson():
    try:
        with open('data/telangana_districts.geojson', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("GeoJSON file not found. Please ensure the file is in the correct location.")
        return None

def main():
    # Create header with logo
    col1, col2 = st.columns([1, 6])
    
    with col1:
        try:
            st.image("assets/telangana_logo.png", width=100)
        except:
            st.markdown("🏛️")  # Fallback if logo not found
    
    with col2:
        st.markdown("# Telangana District Analysis Dashboard")
        st.markdown("**Interactive visualization and analysis of district-wise data in Telangana**")
    
    # Add a separator line
    st.markdown("---")
    
    # Load GeoJSON data
    geojson_data = load_geojson()
    if geojson_data is None:
        st.stop()
    
    # Initialize utilities
    data_processor = DataProcessor()
    map_utils = MapUtils(geojson_data)
    chart_utils = ChartUtils()
    
    # Sidebar for controls
    with st.sidebar:
        st.header("📊 Data Controls")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload CSV file with district-wise data",
            type=['csv'],
            help="CSV should contain a column with district names matching the map districts"
        )
        
        if uploaded_file is not None:
            # Process uploaded data
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.uploaded_data = df
                st.success(f"✅ Data uploaded successfully! ({len(df)} rows)")
                
                # Display basic info about the dataset
                with st.expander("📋 Dataset Info"):
                    st.write(f"**Rows:** {len(df)}")
                    st.write(f"**Columns:** {len(df.columns)}")
                    st.write("**Column names:**")
                    for col in df.columns:
                        st.write(f"- {col}")
                
            except Exception as e:
                st.error(f"❌ Error reading CSV file: {str(e)}")
                st.session_state.uploaded_data = None
        
        # Distance Calculator in Sidebar
        st.header("📏 Distance Calculator")
        map_districts = [feature['properties']['district'] for feature in geojson_data['features']]
        map_districts_sorted = sorted(map_districts)
        
        district_from_sidebar = st.selectbox(
            "From District",
            ["Select District"] + map_districts_sorted,
            key="sidebar_dist_from"
        )
        
        district_to_sidebar = st.selectbox(
            "To District", 
            ["Select District"] + map_districts_sorted,
            key="sidebar_dist_to"
        )
        
        if st.button("Calculate Distance", key="sidebar_calc_dist"):
            if district_from_sidebar != "Select District" and district_to_sidebar != "Select District":
                if district_from_sidebar != district_to_sidebar:
                    map_utils = MapUtils(geojson_data)
                    distance = map_utils.calculate_distance_between_districts(district_from_sidebar, district_to_sidebar)
                    if distance:
                        st.success(f"📏 {distance:.2f} km")
                        st.session_state.show_distance_map = True
                        st.session_state.distance_from = district_from_sidebar
                        st.session_state.distance_to = district_to_sidebar
                    else:
                        st.error("Unable to calculate distance.")
                else:
                    st.warning("Select different districts.")
            else:
                st.warning("Select both districts.")
    
    # Main content area
    if st.session_state.uploaded_data is not None:
        df = st.session_state.uploaded_data
        
        # Data configuration
        st.header("🔧 Data Configuration")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # District column selection
            district_columns = data_processor.find_district_columns(df)
            if district_columns:
                district_col = st.selectbox(
                    "Select District Column",
                    district_columns,
                    help="Column containing district names"
                )
            else:
                district_col = st.selectbox(
                    "Select District Column",
                    df.columns,
                    help="Column containing district names"
                )
        
        with col2:
            # Metric column selection for map visualization
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_columns:
                metric_col = st.selectbox(
                    "Select Metric for Map",
                    ["None"] + numeric_columns,
                    help="Numeric column to visualize on the map with color coding"
                )
            else:
                metric_col = "None"
                st.warning("No numeric columns found for map visualization")
        
        with col3:
            # Color scheme selection
            color_schemes = ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Blues', 'Reds', 'Greens']
            color_scheme = st.selectbox(
                "Color Scheme",
                color_schemes,
                help="Color scheme for map visualization"
            )
        
        # Process and match district data
        matched_data = data_processor.match_districts(df, district_col, geojson_data)
        
        if matched_data is not None and not matched_data.empty:
            st.success(f"✅ Matched {len(matched_data)} districts with map data")
            
            # Map visualization
            st.header("🗺️ Interactive District Map")
            
            # Create map
            if metric_col != "None":
                map_obj = map_utils.create_choropleth_map(matched_data, metric_col, color_scheme)
                st.session_state.map_data = matched_data
            else:
                map_obj = map_utils.create_basic_map()
            
            # Display map
            map_data = st_folium(
                map_obj,
                width=1200,
                height=600,
                returned_objects=["last_clicked"]
            )
            
            # Handle district selection from map click
            if map_data['last_clicked'] is not None:
                clicked_lat = map_data['last_clicked']['lat']
                clicked_lng = map_data['last_clicked']['lng']
                selected_district = map_utils.get_district_from_coordinates(
                    clicked_lat, clicked_lng, geojson_data
                )
                if selected_district:
                    st.session_state.selected_district = selected_district
            
            # District selection dropdown (alternative to map clicking)
            st.header("🎯 District Analysis")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                available_districts = matched_data[district_col].unique().tolist()
                selected_district_dropdown = st.selectbox(
                    "Select District for Analysis",
                    ["None"] + available_districts,
                    index=0 if st.session_state.selected_district is None 
                          else available_districts.index(st.session_state.selected_district) + 1
                          if st.session_state.selected_district in available_districts else 0
                )
                
                if selected_district_dropdown != "None":
                    st.session_state.selected_district = selected_district_dropdown
            
            # Display selected district data
            if st.session_state.selected_district:
                district_data = matched_data[matched_data[district_col] == st.session_state.selected_district]
                
                if not district_data.empty:
                    st.subheader(f"📊 Data for {st.session_state.selected_district}")
                    
                    # Display district data in a nice format
                    district_info = district_data.iloc[0]
                    
                    # Create metrics display
                    metrics_cols = st.columns(min(4, len(numeric_columns)))
                    for i, col in enumerate(numeric_columns[:4]):
                        with metrics_cols[i]:
                            value = district_info[col]
                            st.metric(
                                label=col,
                                value=f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
                            )
                    
                    # Show detailed data table
                    with st.expander("📋 Detailed District Data"):
                        st.dataframe(district_data)
            
            # Charts and Analysis
            st.header("📈 Data Analysis & Visualization")
            
            # Chart type selection
            col1, col2 = st.columns(2)
            with col1:
                chart_type = st.selectbox(
                    "Select Chart Type",
                    ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot", "Box Plot"]
                )
            
            with col2:
                if chart_type in ["Bar Chart", "Line Chart", "Scatter Plot", "Box Plot"]:
                    y_axis_col = st.selectbox(
                        "Select Y-axis Column",
                        numeric_columns,
                        help="Numeric column for Y-axis"
                    )
                elif chart_type == "Pie Chart":
                    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
                    if categorical_cols:
                        pie_col = st.selectbox(
                            "Select Category Column",
                            categorical_cols,
                            help="Categorical column for pie chart"
                        )
                    else:
                        st.warning("No categorical columns found for pie chart")
                        pie_col = None
            
            # Generate charts
            if chart_type == "Bar Chart" and y_axis_col:
                fig = chart_utils.create_bar_chart(matched_data, district_col, y_axis_col)
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Line Chart" and y_axis_col:
                fig = chart_utils.create_line_chart(matched_data, district_col, y_axis_col)
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Pie Chart" and pie_col:
                fig = chart_utils.create_pie_chart(matched_data, pie_col)
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Scatter Plot" and y_axis_col:
                if len(numeric_columns) > 1:
                    x_axis_col = st.selectbox(
                        "Select X-axis Column",
                        [col for col in numeric_columns if col != y_axis_col]
                    )
                    fig = chart_utils.create_scatter_plot(matched_data, x_axis_col, y_axis_col, district_col)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Need at least 2 numeric columns for scatter plot")
            
            elif chart_type == "Box Plot" and y_axis_col:
                fig = chart_utils.create_box_plot(matched_data, y_axis_col)
                st.plotly_chart(fig, use_container_width=True)
            
            # Data summary statistics
            st.header("📋 Data Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Descriptive Statistics")
                if numeric_columns:
                    stats_df = matched_data[numeric_columns].describe()
                    st.dataframe(stats_df)
            
            with col2:
                st.subheader("🔍 Data Overview")
                st.write(f"**Total Districts:** {len(matched_data)}")
                st.write(f"**Total Columns:** {len(matched_data.columns)}")
                st.write(f"**Numeric Columns:** {len(numeric_columns)}")
                
                # Missing data info
                missing_data = matched_data.isnull().sum()
                if missing_data.sum() > 0:
                    st.write("**Missing Data:**")
                    for col, missing_count in missing_data.items():
                        if missing_count > 0:
                            st.write(f"- {col}: {missing_count} missing values")
                else:
                    st.write("**Missing Data:** None")
            
            # Export functionality
            st.header("💾 Export Data")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Download Processed Data as CSV"):
                    csv = matched_data.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="telangana_districts_analysis.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("📊 Download Summary Statistics"):
                    if numeric_columns:
                        stats_csv = matched_data[numeric_columns].describe().to_csv()
                        st.download_button(
                            label="Download Statistics",
                            data=stats_csv,
                            file_name="telangana_districts_statistics.csv",
                            mime="text/csv"
                        )
            
            # Show distance map if requested from sidebar
            if st.session_state.show_distance_map and st.session_state.distance_from and st.session_state.distance_to:
                st.header(f"🗺️ Distance Map: {st.session_state.distance_from} ↔ {st.session_state.distance_to}")
                distance_map = map_utils.create_distance_map(st.session_state.distance_from, st.session_state.distance_to)
                st_folium(
                    distance_map,
                    width=1200,
                    height=500
                )
                if st.button("Hide Distance Map"):
                    st.session_state.show_distance_map = False
        
        else:
            st.error("❌ Could not match district names with map data. Please check your district column.")
            st.info("💡 Make sure district names in your CSV match the names in the map data.")
            
            # Show available districts from map
            with st.expander("🗺️ Available Districts in Map"):
                map_districts = [feature['properties']['district'] for feature in geojson_data['features']]
                for district in sorted(map_districts):
                    st.write(f"- {district}")
    
    else:
        # Show default map when no data is uploaded
        st.header("🗺️ Telangana Districts Map")
        st.info("📤 Upload a CSV file using the sidebar to start analyzing district-wise data!")
        
        # Create basic map
        map_utils = MapUtils(geojson_data)
        basic_map = map_utils.create_basic_map()
        
        st_folium(
            basic_map,
            width=1200,
            height=600
        )
        
        # Distance Calculator
        st.header("📏 District Distance Calculator")
        st.info("Calculate the distance between any two districts in Telangana")
        
        map_districts = [feature['properties']['district'] for feature in geojson_data['features']]
        map_districts_sorted = sorted(map_districts)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            district_from = st.selectbox(
                "From District",
                ["Select District"] + map_districts_sorted,
                key="dist_from"
            )
        
        with col2:
            district_to = st.selectbox(
                "To District", 
                ["Select District"] + map_districts_sorted,
                key="dist_to"
            )
        
        with col3:
            if st.button("🗺️ Calculate Distance", type="primary"):
                if district_from != "Select District" and district_to != "Select District":
                    if district_from != district_to:
                        distance = map_utils.calculate_distance_between_districts(district_from, district_to)
                        if distance:
                            st.success(f"📏 Distance: **{distance:.2f} km**")
                            
                            # Show distance map
                            distance_map = map_utils.create_distance_map(district_from, district_to)
                            st.subheader(f"🗺️ Route from {district_from} to {district_to}")
                            st_folium(
                                distance_map,
                                width=1200,
                                height=500
                            )
                        else:
                            st.error("Unable to calculate distance. Please check district names.")
                    else:
                        st.warning("Please select two different districts.")
                else:
                    st.warning("Please select both districts.")
        
        # Show available districts
        st.header("📍 Available Districts")
        
        cols = st.columns(3)
        for i, district in enumerate(map_districts_sorted):
            with cols[i % 3]:
                st.write(f"• {district}")

if __name__ == "__main__":
    main()
