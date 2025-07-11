# Telangana District Analysis Dashboard

## Overview

This is a Streamlit-based interactive dashboard for analyzing district-wise data in Telangana state, India. The application provides geospatial visualization capabilities using maps and charts to help users understand district-level patterns and trends in uploaded datasets.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for web application interface
- **Visualization Libraries**: 
  - Folium for interactive maps
  - Plotly for interactive charts and graphs
  - streamlit-folium for Streamlit-Folium integration
- **Data Handling**: Pandas for data manipulation and analysis

### Backend Architecture
- **Main Application**: Single-file Streamlit app (`app.py`) serving as the entry point
- **Utility Modules**: Modular design with specialized utility classes:
  - `DataProcessor`: Handles data cleaning, normalization, and district matching
  - `MapUtils`: Manages map creation and geospatial operations
  - `ChartUtils`: Creates various chart visualizations

### Data Storage Solutions
- **Static Data**: GeoJSON file (`data/telangana_districts.geojson`) containing district boundaries
- **Session State**: Streamlit session state for temporary data storage
- **File Upload**: Dynamic CSV/Excel file upload capability for user data

## Key Components

### Data Processing Layer (`utils/data_processor.py`)
- **Problem**: Need to match user-uploaded district data with standardized district names
- **Solution**: Fuzzy string matching and data normalization algorithms
- **Features**:
  - Automatic district column detection
  - District name normalization (removing prefixes/suffixes)
  - Fuzzy matching between user data and GeoJSON district names

### Mapping Layer (`utils/map_utils.py`)
- **Problem**: Need to create interactive geospatial visualizations
- **Solution**: Folium-based mapping with choropleth capabilities
- **Features**:
  - Basic district boundary maps
  - Choropleth maps for data visualization
  - Interactive tooltips and popups
  - Configurable color schemes
  - Distance calculation between districts using Haversine formula
  - Visual distance maps with route lines and markers

### Visualization Layer (`utils/chart_utils.py`)
- **Problem**: Need complementary statistical visualizations
- **Solution**: Plotly-based chart generation
- **Features**:
  - Bar charts for categorical data
  - Line charts for trend analysis
  - Customizable color palettes
  - Interactive hover data

### Main Application (`app.py`)
- **Problem**: Need to orchestrate all components into a cohesive user interface
- **Solution**: Streamlit dashboard with modular component integration
- **Features**:
  - File upload interface
  - Interactive map display
  - Chart generation and display
  - Session state management
  - District distance calculator with visual route display
  - Integrated sidebar controls for quick distance calculations

## Data Flow

1. **Data Ingestion**: User uploads CSV/Excel files through Streamlit interface
2. **Data Processing**: DataProcessor normalizes and matches district names with GeoJSON data
3. **Visualization Generation**: 
   - MapUtils creates choropleth maps based on processed data
   - ChartUtils generates complementary statistical charts
4. **Interactive Display**: Streamlit renders maps and charts with user interaction capabilities
5. **State Management**: Session state maintains user selections and uploaded data across interactions

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **folium**: Interactive mapping
- **plotly**: Interactive plotting
- **fuzzywuzzy**: Fuzzy string matching

### Geospatial Dependencies
- **shapely**: Geometric operations (used in map_utils.py)
- **streamlit-folium**: Streamlit-Folium integration

### Data Sources
- **Static GeoJSON**: Telangana district boundaries file
- **User Data**: Dynamic CSV/Excel uploads

## Deployment Strategy

### Development Environment
- **Platform**: Designed for Streamlit deployment
- **Structure**: Modular architecture for easy maintenance and testing
- **Configuration**: Page configuration optimized for wide layout and expanded sidebar

### Production Considerations
- **Caching**: Uses `@st.cache_data` decorator for GeoJSON loading optimization
- **Error Handling**: Graceful handling of missing files and data errors
- **User Experience**: Progress indicators and error messages for better UX

### Scalability Features
- **Modular Design**: Separate utility classes for easy extension
- **Configurable Components**: Color schemes, map parameters, and chart types are customizable
- **Session Management**: Efficient state management for user interactions

## Recent Changes

### Theme Switching Feature (July 11, 2025)
- Added dark/light mode toggle in sidebar settings
- Implemented custom CSS theming for better user experience
- Enhanced logo visibility with theme-aware styling
- Created themed metric cards and styling components
- Added professional theme transition effects

### District Distance Calculator (July 11, 2025)
- Added geographic distance calculation using Haversine formula
- Implemented visual distance maps showing routes between districts
- Added dual interface: sidebar quick calculator and main section detailed view
- Enhanced map utilities with centroid calculation and distance visualization
- Color-coded district highlighting (blue/red) with purple route lines

The application follows a clean separation of concerns with the main app orchestrating specialized utility classes, making it easy to extend functionality or modify individual components without affecting the entire system.