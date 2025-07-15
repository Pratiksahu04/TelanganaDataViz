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
from utils.chart_utils import ChartUtils # Ensure this file exists and is updated

# --- Page Configuration ---
st.set_page_config(
    page_title="Telangana District Analysis | RBI", # More specific title
    page_icon="🇮🇳", # Indian flag icon
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialize Session State ---
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
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
# Add new session state for selected_district_col if not already present
if 'selected_district_col' not in st.session_state:
    st.session_state.selected_district_col = None


# --- Load GeoJSON Data ---
@st.cache_data
def load_geojson():
    try:
        with open('data/telangana_districts.geojson', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Error: Telangana GeoJSON file not found. Please ensure 'telangana_districts.geojson' is in the 'data' directory.")
        return None

# --- Theme Application ---
def apply_theme():
    """Apply professional theme-specific CSS styling for RBI context."""
    if st.session_state.dark_mode:
        # Dark theme for a sophisticated look
        st.markdown("""
        <style>
        body { font-family: 'Arial', sans-serif; }
        .stApp {
            background-color: #1e212b; /* Deep charcoal */
            color: #e0e0e0; /* Off-white text */
        }
        .logo-container {
            background-color: #2a2e3a; /* Slightly lighter charcoal for contrast */
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #444;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3); /* Softer shadow */
            text-align: center;
            margin: 15px 0;
        }
        .main-header h1, .main-header h2, .main-header h3 {
            color: #ffffff; /* Pure white for main headers */
            font-weight: 600;
        }
        .main-header h1 { font-size: 2.5em; margin-bottom: 0.1em; }
        .main-header p { color: #a0a0a0; font-size: 1.1em; }

        /* General Streamlit widget styling */
        .stButton>button {
            background-color: #4CAF50; /* Green for primary action */
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 8px;
            transition-duration: 0.4s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .stButton>button:hover {
            background-color: #45a049;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        .stButton>button[data-baseweb="button"] { /* For secondary buttons like theme switch */
             background-color: #555;
             color: white;
             border: 1px solid #777;
        }
        .stButton>button[data-baseweb="button"]:hover {
             background-color: #666;
             border: 1px solid #999;
        }

        .stSelectbox>div>div {
            background-color: #2a2e3a;
            color: #e0e0e0;
            border: 1px solid #444;
            border-radius: 8px;
        }
        .stSelectbox>div>div:hover {
            border-color: #666;
        }
        .stSelectbox div[role="listbox"] {
            background-color: #2a2e3a; /* Dropdown list background */
            border: 1px solid #444;
            color: #e0e0e0;
        }
        .stSelectbox div[role="option"]:hover {
            background-color: #3a3e4a; /* Hover on dropdown options */
        }
        .stText, .stMarkdown {
            color: #e0e0e0;
        }
        .stPlotlyChart {
            border-radius: 8px;
            overflow: hidden; /* Ensures borders are respected */
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        /* Custom metric cards */
        .metric-card {
            background-color: #2a2e3a; /* Matches logo container */
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #444;
            margin: 8px 0;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease-in-out;
        }
        .metric-card:hover {
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
            transform: translateY(-2px);
        }
        .metric-card h4 {
            color: #a0a0a0; /* Subtler title for metric */
            font-size: 0.9em;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-card h2 {
            color: #e0e0e0; /* Metric value color */
            font-size: 2.2em;
            font-weight: 700;
            margin-top: 0;
            line-height: 1.2;
        }
        .stSpinner > div {
            border-color: #4CAF50 !important;
            border-top-color: transparent !important;
        }
        .stProgress > div > div > div > div {
            background-color: #4CAF50 !important;
        }
        .css-1d391kg.e1nzilvr3 { /* Streamlit header element */
            color: #e0e0e0;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light theme for a clean, corporate look
        st.markdown("""
        <style>
        body { font-family: 'Arial', sans-serif; }
        .stApp {
            background-color: #f0f2f6; /* Very light gray */
            color: #333333; /* Dark gray text */
        }
        .logo-container {
            background-color: #ffffff;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            text-align: center;
            margin: 15px 0;
        }
        .main-header h1, .main-header h2, .main-header h3 {
            color: #2c3e50; /* Dark blue-gray for main headers */
            font-weight: 600;
        }
        .main-header h1 { font-size: 2.5em; margin-bottom: 0.1em; }
        .main-header p { color: #555555; font-size: 1.1em; }

        /* General Streamlit widget styling */
        .stButton>button {
            background-color: #007bff; /* Primary blue */
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 8px;
            transition-duration: 0.4s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .stButton>button:hover {
            background-color: #0056b3;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .stButton>button[data-baseweb="button"] { /* For secondary buttons like theme switch */
             background-color: #cccccc;
             color: #333;
             border: 1px solid #aaaaaa;
        }
        .stButton>button[data-baseweb="button"]:hover {
             background-color: #bbbbbb;
             border: 1px solid #888888;
        }

        .stSelectbox>div>div {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #ccc;
            border-radius: 8px;
        }
        .stSelectbox>div>div:hover {
            border-color: #999;
        }
        .stSelectbox div[role="listbox"] {
            background-color: #ffffff; /* Dropdown list background */
            border: 1px solid #ccc;
            color: #333333;
        }
        .stSelectbox div[role="option"]:hover {
            background-color: #f0f0f0; /* Hover on dropdown options */
        }
        .stText, .stMarkdown {
            color: #333333;
        }
        .stPlotlyChart {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        /* Custom metric cards */
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            margin: 8px 0;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease-in-out;
        }
        .metric-card:hover {
            box_shadow: 0 6px 12px rgba(0,0,0,0.2);
            transform: translateY(-2px);
        }
        .metric-card h4 {
            color: #555555;
            font-size: 0.9em;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-card h2 {
            color: #2c3e50;
            font-size: 2.2em;
            font-weight: 700;
            margin-top: 0;
            line-height: 1.2;
        }
        .stSpinner > div {
            border-color: #007bff !important;
            border-top-color: transparent !important;
        }
        .stProgress > div > div > div > div {
            background-color: #007bff !important;
        }
        .css-1d391kg.e1nzilvr3 { /* Streamlit header element */
            color: #2c3e50;
        }
        </style>
        """, unsafe_allow_html=True)

# --- Main Application Function ---
def main():
    apply_theme()
    
    # Header with Logo and Title
    header_col1, header_col2, header_col3 = st.columns([1, 6, 1])
    
    with header_col1:
        try:
            st.markdown('<div class="logo-container">', unsafe_allow_html=True)
            st.image("assets/telangana_logo.png", width=100) # Ensure this logo path is correct
            st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.markdown("🏛️") # Fallback if logo not found
    
    with header_col2:
        st.markdown('<div class="main-header">', unsafe_allow_html=True)
        st.markdown("<h1>Telangana District Data Insights</h1>", unsafe_allow_html=True)
        st.markdown("<p>Interactive analysis and visualization for the Reserve Bank of India</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with header_col3:
        st.empty() # For spacing or future use

    st.divider() # Professional separator

    # Load GeoJSON data
    geojson_data = load_geojson()
    if geojson_data is None:
        st.stop()
    
    # Initialize utilities
    data_processor = DataProcessor()
    map_utils = MapUtils(geojson_data)
    chart_utils = ChartUtils() # ChartUtils instance

    # --- Sidebar for Controls ---
    with st.sidebar:
        st.markdown("## ⚙️ Application Settings")
        
        # Theme toggle
        theme_col1, theme_col2 = st.columns([1, 1])
        with theme_col1:
            if st.button("🌙 Dark Mode", key="dark_btn", use_container_width=True, 
                        type="primary" if st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = True
                st.rerun()
        
        with theme_col2:
            if st.button("☀️ Light Mode", key="light_btn", use_container_width=True,
                        type="primary" if not st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = False
                st.rerun()
        
        st.divider() # Separator

        st.markdown("## 📥 Data Management")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload District-wise CSV Data",
            type=['csv'],
            help="Upload a CSV file containing district-level economic or demographic data for Telangana. Ensure a column with district names is present."
        )
        
        if uploaded_file is not None:
            # Process uploaded data
            try:
                df = pd.read_csv(uploaded_file)
                if "Sn" in df.columns:
                    df = df.drop(columns=["Sn"])
                st.session_state.uploaded_data = df
                st.success(f"✅ Data uploaded successfully! ({len(df)} rows, {len(df.columns)} columns)")
                
                # Display basic info about the dataset
                with st.expander("📊 View Raw Dataset Info"):
                    st.dataframe(df.head()) # Show head of the dataframe
                    st.write(f"**Total Rows:** {len(df)}")
                    st.write(f"**Total Columns:** {len(df.columns)}")
                    st.write("**Identified Columns:**")
                    for col in df.columns:
                        st.write(f"- `{col}` (Type: `{df[col].dtype}`)")
                
            except Exception as e:
                st.error(f"❌ Error reading CSV file: {str(e)}")
                st.session_state.uploaded_data = None
        
        st.divider() # Separator

        # Distance Calculator in Sidebar
        st.markdown("## 🌍 Inter-District Distance Calculator")
        map_districts = [feature['properties']['district'] for feature in geojson_data['features']]
        map_districts_sorted = sorted(map_districts)
        
        district_from_sidebar = st.selectbox(
            "Origin District",
            ["Select District"] + map_districts_sorted,
            key="sidebar_dist_from",
            help="Select the starting district."
        )
        
        district_to_sidebar = st.selectbox(
            "Destination District", 
            ["Select District"] + map_districts_sorted,
            key="sidebar_dist_to",
            help="Select the ending district."
        )
        
        if st.button("Calculate Route Distance", key="sidebar_calc_dist", type="primary", use_container_width=True):
            if district_from_sidebar != "Select District" and district_to_sidebar != "Select District":
                if district_from_sidebar != district_to_sidebar:
                    with st.spinner("Calculating distance..."):
                        distance = map_utils.calculate_distance_between_districts(district_from_sidebar, district_to_sidebar)
                        if distance:
                            st.success(f"📏 Distance: **{distance:.2f} km**")
                            st.session_state.show_distance_map = True
                            st.session_state.distance_from = district_from_sidebar
                            st.session_state.distance_to = district_to_sidebar
                        else:
                            st.error("Unable to calculate distance. Please verify district names.")
                else:
                    st.warning("Please select two *different* districts for calculation.")
            else:
                st.warning("Please select both origin and destination districts.")
    
    # --- Main Content Area ---
    st.markdown("## 📈 Data Insights and Visualizations")
    
    if st.session_state.uploaded_data is not None:
        df = st.session_state.uploaded_data
        
        # --- Data Configuration (Dynamically select district column) ---
        st.subheader("Dataset Configuration")
        
        # Use data_processor to find potential district columns
        potential_district_cols = data_processor.find_district_columns(df)
        
        if not potential_district_cols:
            st.error("❌ No potential district columns found in your data. Please ensure one column contains district names.")
            st.stop()

        # Try to automatically select 'District' or the first identified column
        if 'District' in potential_district_cols:
            default_district_col_index = potential_district_cols.index('District')
        else:
            default_district_col_index = 0

        # Allow user to select district column if auto-detection is wrong
        district_col = st.selectbox(
            "Select the column containing District Names for Mapping:",
            options=potential_district_cols,
            index=default_district_col_index,
            help="This column will be used to link your data to the Telangana map.",
            key="district_col_selector"
        )
        st.session_state.selected_district_col = district_col # Store in session state

        # Also provide a selection for the metric column for the map, making it dynamic
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_columns:
            st.error("❌ No numeric columns found in your data for map visualization. Please ensure your CSV has numerical data.")
            st.stop()

        # Try to auto-select 'Geographical Area (Sq km)' or the first numeric column
        default_metric_index = 0
        if 'Geographical Area (Sq km)' in numeric_columns:
            default_metric_index = numeric_columns.index('Geographical Area (Sq km)')
        elif 'Area' in numeric_columns: # Fallback for common area names
            default_metric_index = numeric_columns.index('Area')


        metric_col = st.selectbox(
            "Select the Metric Column for Map Visualization:",
            options=numeric_columns,
            index=default_metric_index,
            help="This numeric column will be used to color the districts on the map.",
            key="map_metric_col_selector"
        )

        color_scheme = st.selectbox(
            "Select Map Color Scheme:",
            ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Blues', 'Reds', 'Greens'],
            index=0, # Default to viridis
            help="Choose a color scheme for the choropleth map.",
            key="map_color_scheme"
        )


        # Process and match district data (verbose=False to suppress fuzzy match messages)
        matched_data = data_processor.match_districts(df, district_col, geojson_data, verbose=False) 
        
        if matched_data is not None and not matched_data.empty:
            st.success(f"✅ Data successfully processed and matched for {len(matched_data)} districts using column '{district_col}'.")
            
            # --- Interactive District Map ---
            st.markdown(f"### Interactive District Map: {metric_col}")
            st.write(f"Explore the geographical distribution of districts, colored by **{metric_col}**.")
            
            # Create map
            map_obj = map_utils.create_choropleth_map(matched_data, metric_col, color_scheme)
            st.session_state.map_data = matched_data
            
            # Display map
            map_data_output = st_folium(
                map_obj,
                width=1200, # Fixed width for professional look
                height=600, # Fixed height
                returned_objects=["last_clicked"],
                key="main_map" # Add a key for consistent behavior
            )
            
            # Handle district selection from map click
            if map_data_output['last_clicked'] is not None:
                clicked_lat = map_data_output['last_clicked']['lat']
                clicked_lng = map_data_output['last_clicked']['lng']
                selected_district_from_map = map_utils.get_district_from_coordinates(
                    clicked_lat, clicked_lng, geojson_data
                )
                if selected_district_from_map:
                    st.session_state.selected_district = selected_district_from_map
                    st.toast(f"📍 Selected {st.session_state.selected_district} from map!")
            
            # --- District-Specific Analysis ---
            st.divider()
            st.markdown("### District-Specific Data Analysis")
            st.write("Select a district from the dropdown or by clicking on the map to view its detailed data and statistics.")

            available_districts = matched_data[district_col].unique().tolist()
            # Set initial index for selectbox
            initial_district_index = 0
            if st.session_state.selected_district and st.session_state.selected_district in available_districts:
                initial_district_index = available_districts.index(st.session_state.selected_district) + 1 # +1 because of "Select District" option

            selected_district_dropdown = st.selectbox(
                "Choose a District",
                ["Select District"] + available_districts,
                index=initial_district_index,
                key="district_analysis_select"
            )
            
            if selected_district_dropdown != "Select District":
                st.session_state.selected_district = selected_district_dropdown
            
            if st.session_state.selected_district and st.session_state.selected_district != "Select District":
                district_data = matched_data[matched_data[district_col] == st.session_state.selected_district]
                
                if not district_data.empty:
                    st.subheader(f"Data Snapshot for {st.session_state.selected_district}")
                    st.write("Key metrics for the selected district:")
                    
                    # Get all numeric columns for metric cards, excluding the district column itself
                    # Make sure to use the original dataframe's columns for general metrics display
                    numeric_columns_for_metrics = [col for col in df.select_dtypes(include=[np.number]).columns.tolist() if col != district_col]
                    
                    # Create metric cards
                    metric_cols_count = min(4, len(numeric_columns_for_metrics)) # Limit to 4 cards per row
                    if metric_cols_count > 0:
                        metrics_rows = st.columns(metric_cols_count)
                        for i, col in enumerate(numeric_columns_for_metrics):
                            with metrics_rows[i % metric_cols_count]:
                                value = district_data.iloc[0][col]
                                
                                display_value = ""
                                if pd.isna(value) or value is None:
                                    display_value = "N/A"
                                elif isinstance(value, float):
                                    display_value = f"{value:,.2f}" # Format floats to 2 decimal places with comma
                                elif isinstance(value, int):
                                    display_value = f"{value:,}" # Format integers with comma
                                else:
                                    display_value = str(value)
                                    
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h4>{col}</h4>
                                    <h2>{display_value}</h2>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("No numeric data available for metric cards in this district.")
                    
                    # Detailed Data Table
                    with st.expander(f"📋 View Full Data Table for {st.session_state.selected_district}"):
                        st.dataframe(district_data, use_container_width=True)
                    
                    # --- Charts and Analysis for Selected District ---
                    st.divider()
                    st.subheader("In-depth Data Visualization")
                    st.write("Generate custom charts to analyze specific data trends or comparisons.")

                    numeric_columns_for_charts = df.select_dtypes(include=[np.number]).columns.tolist() # Get all numeric columns
                    categorical_columns_for_charts = df.select_dtypes(include=['object']).columns.tolist()

                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        chart_type = st.selectbox(
                            "Select Chart Type",
                            ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot", "Box Plot", "Multi-Metric Line Chart", "Ranking Chart"], # Added new types
                            key="chart_type_select"
                        )
                    
                    # Dynamic column selection based on chart type
                    with chart_col2:
                        y_axis_col, x_axis_col, pie_col, multi_metric_cols, ranking_metric_col = None, None, None, None, None

                        if chart_type in ["Bar Chart", "Line Chart", "Box Plot"]:
                            if numeric_columns_for_charts:
                                y_axis_col = st.selectbox(
                                    "Select Value (Y-axis) Column",
                                    numeric_columns_for_charts,
                                    help="Numeric column for Y-axis",
                                    key="y_axis_select"
                                )
                            else:
                                st.warning("No numeric columns found for this chart type.")
                        elif chart_type == "Scatter Plot":
                            if len(numeric_columns_for_charts) >= 2:
                                y_axis_col = st.selectbox(
                                    "Select Y-axis Column",
                                    numeric_columns_for_charts,
                                    key="scatter_y_select"
                                )
                                x_axis_col = st.selectbox(
                                    "Select X-axis Column",
                                    [col for col in numeric_columns_for_charts if col != y_axis_col],
                                    key="scatter_x_select"
                                )
                            else:
                                st.warning("Need at least 2 numeric columns for Scatter Plot.")
                        elif chart_type == "Pie Chart":
                            if categorical_columns_for_charts:
                                pie_col = st.selectbox(
                                    "Select Category Column",
                                    categorical_columns_for_charts,
                                    help="Categorical column for pie chart",
                                    key="pie_col_select"
                                )
                                # For pie chart, we usually count occurrences or sum another column
                                pie_value_col_options = ['Count of Records'] + numeric_columns_for_charts
                                pie_value_col = st.selectbox(
                                    "Select Value for Pie Chart:",
                                    pie_value_col_options,
                                    index=0,
                                    help="Choose 'Count of Records' or a numeric column to sum/average for pie slices.",
                                    key="pie_value_select"
                                )
                            else:
                                st.warning("No categorical columns found for Pie Chart.")
                        elif chart_type == "Multi-Metric Line Chart":
                            if numeric_columns_for_charts:
                                multi_metric_cols = st.multiselect(
                                    "Select Metrics to Compare",
                                    numeric_columns_for_charts,
                                    default=numeric_columns_for_charts[:2] if len(numeric_columns_for_charts) >= 2 else numeric_columns_for_charts,
                                    help="Select multiple numeric columns to compare their trends across districts.",
                                    key="multi_metric_select"
                                )
                            else:
                                st.warning("No numeric columns found for Multi-Metric Line Chart.")
                        elif chart_type == "Ranking Chart":
                            if numeric_columns_for_charts:
                                ranking_metric_col = st.selectbox(
                                    "Select Metric for Ranking",
                                    numeric_columns_for_charts,
                                    help="Select a numeric column to rank districts by.",
                                    key="ranking_metric_select"
                                )
                                top_n = st.slider(
                                    "Show Top/Bottom N Districts",
                                    min_value=1,
                                    max_value=len(matched_data),
                                    value=min(10, len(matched_data)),
                                    key="top_n_slider"
                                )
                                ranking_ascending = st.checkbox(
                                    "Rank Ascending (Bottom N)",
                                    value=False,
                                    help="Check to show bottom N districts (lowest values), uncheck for top N (highest values).",
                                    key="ranking_ascending_checkbox"
                                )
                            else:
                                st.warning("No numeric columns found for Ranking Chart.")
                    
                    # Generate charts
                    if chart_type == "Bar Chart" and y_axis_col:
                        fig = chart_utils.create_bar_chart(matched_data, district_col, y_axis_col, title=f'{y_axis_col} per District')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Line Chart" and y_axis_col:
                        fig = chart_utils.create_line_chart(matched_data, district_col, y_axis_col, title=f'{y_axis_col} Trend Across Districts')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Pie Chart" and pie_col and pie_value_col:
                        if pie_value_col == 'Count of Records':
                            # Create a temporary DataFrame for counts for the pie chart
                            pie_df = matched_data[pie_col].value_counts().reset_index()
                            pie_df.columns = [pie_col, 'Count']
                            fig = chart_utils.create_pie_chart(pie_df, pie_col, 'Count', title=f'Distribution by {pie_col}')
                        else:
                            # For other numeric values, sum/average by category if needed, or use directly if single value
                            # Assuming you want to show the distribution of a numeric column across categories for pie.
                            # If `matched_data` needs aggregation first, do it here.
                            # For simplicity, if pie_value_col is a numeric column, we can use it directly if it's already aggregated (e.g. per district).
                            # If not, you might want to sum/mean it per category. Let's assume for now it's per category.
                            fig = chart_utils.create_pie_chart(matched_data, pie_col, pie_value_col, title=f'Distribution of {pie_value_col} by {pie_col}')

                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Scatter Plot" and x_axis_col and y_axis_col:
                        fig = chart_utils.create_scatter_plot(matched_data, x_axis_col, y_axis_col, color_col=district_col, title=f'{y_axis_col} vs {x_axis_col} by District')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Box Plot" and y_axis_col:
                        fig = chart_utils.create_box_plot(matched_data, y_axis_col, x_col=district_col, title=f'Distribution of {y_axis_col} Across Districts') # Changed x_col to district_col for box plot
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Multi-Metric Line Chart" and multi_metric_cols:
                        if len(multi_metric_cols) > 0:
                            fig = chart_utils.create_multi_metric_line_chart(matched_data, district_col, multi_metric_cols)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Please select at least one metric for the Multi-Metric Line Chart.")
                    
                    elif chart_type == "Ranking Chart" and ranking_metric_col:
                        fig = chart_utils.create_ranking_chart(matched_data, district_col, ranking_metric_col, top_n, ranking_ascending)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    else:
                        st.info("Please select a chart type and appropriate columns to generate the visualization.")

            # --- Data Summary Statistics ---
            st.divider()
            st.markdown("### Comprehensive Data Summary")
            
            summary_col1, summary_col2 = st.columns(2)
            
            with summary_col1:
                st.subheader("Descriptive Statistics (Numeric Columns)")
                numeric_columns_summary = df.select_dtypes(include=[np.number]).columns # Use original numeric columns for summary
                if not numeric_columns_summary.empty:
                    stats_df = matched_data[numeric_columns_summary].describe().transpose() # Transpose for better readability
                    st.dataframe(stats_df)
                else:
                    st.info("No numeric columns available for descriptive statistics.")
            
            with summary_col2:
                st.subheader("Dataset Overview")
                st.write(f"**Total Records Processed:** {len(matched_data):,} rows")
                st.write(f"**Total Columns Analyzed:** {len(matched_data.columns)} columns")
                st.write(f"**Numeric Data Series:** {len(df.select_dtypes(include=[np.number]).columns)} columns")
                st.write(f"**Categorical Data Series:** {len(df.select_dtypes(include=['object', 'category']).columns)} columns")
                
                # Missing data info
                missing_data = matched_data.isnull().sum()
                total_missing = missing_data.sum()
                if total_missing > 0:
                    st.warning(f"⚠️ **Total Missing Values:** {total_missing:,}")
                    with st.expander("View Missing Values by Column"):
                        for col, missing_count in missing_data.items():
                            if missing_count > 0:
                                st.write(f"- `{col}`: {missing_count:,} missing values ({missing_count / len(matched_data) * 100:.2f}%)")
                else:
                    st.success("✅ No missing values detected in the processed dataset.")
            
            # --- Export Functionality ---
            st.divider()
            st.markdown("### Data Export Options")
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                st.download_button(
                    label="📥 Download Processed Data (CSV)",
                    data=matched_data.to_csv(index=False).encode('utf-8'),
                    file_name="telangana_district_analysis_processed_data.csv",
                    mime="text/csv",
                    help="Download the cleaned and matched dataset."
                )
            
            with export_col2:
                numeric_columns_for_download = df.select_dtypes(include=[np.number]).columns # Use original numeric columns
                if not numeric_columns_for_download.empty:
                    stats_csv = matched_data[numeric_columns_for_download].describe().transpose().to_csv().encode('utf-8')
                    st.download_button(
                        label="📊 Download Summary Statistics (CSV)",
                        data=stats_csv,
                        file_name="telangana_district_summary_statistics.csv",
                        mime="text/csv",
                        help="Download descriptive statistics for numeric columns."
                    )
                else:
                    st.info("No numeric data for statistics download.")
            
            # --- Show Distance Map if triggered from sidebar ---
            if st.session_state.show_distance_map and st.session_state.distance_from and st.session_state.distance_to:
                st.divider()
                st.markdown(f"### 🗺️ Route Analysis: {st.session_state.distance_from} ↔ {st.session_state.distance_to}")
                with st.spinner(f"Generating map for {st.session_state.distance_from} to {st.session_state.distance_to}..."):
                    distance_map = map_utils.create_distance_map(st.session_state.distance_from, st.session_state.distance_to)
                    st_folium(
                        distance_map,
                        width=1200,
                        height=500,
                        key="distance_map_display"
                    )
                if st.button("Hide Route Map", key="hide_distance_map_btn"):
                    st.session_state.show_distance_map = False
                    st.rerun()
        
        else:
            st.error("❌ Data matching failed. Please ensure your CSV has a column with district names that can be mapped to Telangana districts.")
            st.info("💡 **Tip:** Verify your selected 'District Column' for typos. You can refer to the 'Available Districts in Map' section below for official names.")
            
            # Show available districts from map
            with st.expander("🌍 Reference: Official Districts in Telangana Map"):
                map_districts = [feature['properties']['district'] for feature in geojson_data['features']]
                # Display in columns for better readability if many districts
                num_cols_display = 4
                cols = st.columns(num_cols_display)
                for i, district in enumerate(sorted(map_districts)):
                    with cols[i % num_cols_display]:
                        st.write(f"• `{district}`")
    
    else:
        # Default view when no data is uploaded
        st.markdown("## 🗺️ Telangana Districts Overview")
        st.info("📤 Please upload your district-wise data CSV using the sidebar to begin detailed analysis. This initial map displays the administrative boundaries of Telangana districts.")
        
        # Create basic map
        map_utils = MapUtils(geojson_data)
        basic_map = map_utils.create_basic_map()
        
        st_folium(
            basic_map,
            width=1200,
            height=600,
            key="default_basic_map"
        )
        
        st.divider()
        st.markdown("## 📏 Inter-District Distance Calculator")
        st.write("Quickly calculate the aerial distance between any two districts in Telangana. Select districts from the dropdowns below.")
        
        map_districts = [feature['properties']['district'] for feature in geojson_data['features']]
        map_districts_sorted = sorted(map_districts)
        
        dist_calc_col1, dist_calc_col2, dist_calc_col3 = st.columns([1, 1, 1])
        
        with dist_calc_col1:
            district_from_main = st.selectbox(
                "From District",
                ["Select District"] + map_districts_sorted,
                key="main_dist_from"
            )
        
        with dist_calc_col2:
            district_to_main = st.selectbox(
                "To District", 
                ["Select District"] + map_districts_sorted,
                key="main_dist_to"
            )
        
        with dist_calc_col3:
            st.markdown("<br>", unsafe_allow_html=True) # Add some space to align button
            if st.button("✨ Calculate Distance & View Map", type="primary", key="main_calc_dist_btn"):
                if district_from_main != "Select District" and district_to_main != "Select District":
                    if district_from_main != district_to_main:
                        with st.spinner(f"Calculating distance between {district_from_main} and {district_to_main}..."):
                            distance = map_utils.calculate_distance_between_districts(district_from_main, district_to_main)
                            if distance:
                                st.success(f"📏 Distance: **{distance:.2f} km**")
                                
                                # Show distance map
                                distance_map = map_utils.create_distance_map(district_from_main, district_to_main)
                                st.subheader(f"🗺️ Visualized Route: {district_from_main} ↔ {district_to_main}")
                                st_folium(
                                    distance_map,
                                    width=1200,
                                    height=500,
                                    key="main_distance_map_display"
                                )
                            else:
                                st.error("Unable to calculate distance. Please check district names.")
                    else:
                        st.warning("Please select two *different* districts for distance calculation.")
                else:
                    st.warning("Please select both origin and destination districts to calculate distance.")
        
        st.divider()
        # Show available districts
        st.markdown("### 📍 Official Districts of Telangana")
        st.write("Reference list of all districts included in the geographical map data.")
        
        cols_per_row = 4
        cols_list = st.columns(cols_per_row)
        for i, district in enumerate(map_districts_sorted):
            with cols_list[i % cols_per_row]:
                st.markdown(f"• `{district}`") # Use backticks for code-like styling of names

if __name__ == "__main__":
    main()
