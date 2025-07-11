import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
import streamlit as st

class DataProcessor:
    def __init__(self):
        pass
    
    def find_district_columns(self, df):
        """
        Automatically identify potential district columns based on column names
        """
        district_keywords = ['district', 'districts', 'dist', 'area', 'region', 'location', 'place', 'city']
        potential_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            for keyword in district_keywords:
                if keyword in col_lower:
                    potential_columns.append(col)
                    break
        
        return potential_columns if potential_columns else df.columns.tolist()
    
    def normalize_district_name(self, name):
        """
        Normalize district names for better matching
        """
        if pd.isna(name):
            return ""
        
        name = str(name).strip()
        # Remove common suffixes and prefixes
        name = name.replace(" District", "").replace(" district", "")
        name = name.replace("District ", "").replace("district ", "")
        
        return name.title()
    
    def match_districts(self, df, district_col, geojson_data):
        """
        Match district names from CSV with GeoJSON data
        """
        if district_col not in df.columns:
            st.error(f"Column '{district_col}' not found in the dataset")
            return None
        
        # Get district names from GeoJSON
        map_districts = [feature['properties']['district'] for feature in geojson_data['features']]
        map_districts_normalized = [self.normalize_district_name(d) for d in map_districts]
        
        # Create a copy of the dataframe
        matched_df = df.copy()
        
        # Normalize district names in the CSV
        matched_df['normalized_district'] = matched_df[district_col].apply(self.normalize_district_name)
        
        # Create a mapping dictionary
        district_mapping = {}
        unmatched_districts = []
        
        for csv_district in matched_df['normalized_district'].unique():
            if csv_district == "":
                continue
                
            # Try exact match first
            if csv_district in map_districts_normalized:
                idx = map_districts_normalized.index(csv_district)
                district_mapping[csv_district] = map_districts[idx]
            else:
                # Try fuzzy matching
                best_match = None
                best_score = 0
                
                for map_district in map_districts_normalized:
                    score = fuzz.ratio(csv_district.lower(), map_district.lower())
                    if score > best_score and score > 80:  # 80% similarity threshold
                        best_score = score
                        best_match = map_district
                
                if best_match:
                    idx = map_districts_normalized.index(best_match)
                    district_mapping[csv_district] = map_districts[idx]
                    st.info(f"🔄 Fuzzy matched '{csv_district}' → '{map_districts[idx]}' (score: {best_score}%)")
                else:
                    unmatched_districts.append(csv_district)
        
        # Apply mapping
        matched_df['matched_district'] = matched_df['normalized_district'].map(district_mapping)
        
        # Filter out unmatched districts
        matched_df = matched_df[matched_df['matched_district'].notna()]
        
        if unmatched_districts:
            st.warning(f"⚠️ Could not match {len(unmatched_districts)} districts: {', '.join(unmatched_districts)}")
        
        if matched_df.empty:
            st.error("❌ No districts could be matched. Please check your district names.")
            return None
        
        # Update the district column with matched names
        matched_df[district_col] = matched_df['matched_district']
        matched_df = matched_df.drop(['normalized_district', 'matched_district'], axis=1)
        
        return matched_df
    
    def validate_data(self, df):
        """
        Validate the uploaded data
        """
        errors = []
        warnings = []
        
        # Check if dataframe is empty
        if df.empty:
            errors.append("The uploaded file is empty")
        
        # Check for missing values
        missing_counts = df.isnull().sum()
        if missing_counts.sum() > 0:
            warnings.append(f"Found {missing_counts.sum()} missing values across {(missing_counts > 0).sum()} columns")
        
        # Check for duplicate rows
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate rows")
        
        return errors, warnings
    
    def clean_data(self, df):
        """
        Basic data cleaning operations
        """
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def get_summary_statistics(self, df):
        """
        Generate summary statistics for the dataset
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        summary = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'numeric_columns': len(numeric_cols),
            'categorical_columns': len(df.columns) - len(numeric_cols),
            'missing_values': df.isnull().sum().sum(),
            'duplicate_rows': df.duplicated().sum()
        }
        
        return summary
