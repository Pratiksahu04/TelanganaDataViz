import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

class ChartUtils:
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def create_bar_chart(self, data, x_col, y_col, title=None):
        """
        Create a bar chart
        """
        if title is None:
            title = f"{y_col} by {x_col}"
        
        fig = px.bar(
            data,
            x=x_col,
            y=y_col,
            title=title,
            color=y_col,
            color_continuous_scale='viridis',
            hover_data=[x_col, y_col]
        )
        
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            showlegend=False,
            height=500,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_line_chart(self, data, x_col, y_col, title=None):
        """
        Create a line chart
        """
        if title is None:
            title = f"{y_col} Trend by {x_col}"
        
        # Sort data by x column for better line visualization
        data_sorted = data.sort_values(x_col)
        
        fig = px.line(
            data_sorted,
            x=x_col,
            y=y_col,
            title=title,
            markers=True,
            hover_data=[x_col, y_col]
        )
        
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            height=500,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_pie_chart(self, data, names_col, values_col, title=None): # Added values_col
        """
        Create a pie chart
        """
        if title is None:
            title = f"Distribution of {values_col} by {names_col}" # More descriptive title
        
        fig = px.pie(
            data, # Pass the DataFrame directly
            names=names_col,
            values=values_col,
            title=title,
            color_discrete_sequence=self.color_palette
        )
        
        fig.update_layout(
            height=500,
            showlegend=True
        )
        
        return fig
    
    def create_scatter_plot(self, data, x_col, y_col, hover_col=None, color_col=None, title=None): # Added color_col
        """
        Create a scatter plot
        """
        if title is None:
            title = f"{y_col} vs {x_col}"
        
        hover_data = [x_col, y_col]
        if hover_col and hover_col in data.columns:
            hover_data.append(hover_col)
        
        # Determine the column to use for coloring
        plot_color_col = color_col if color_col and color_col in data.columns else None
        
        fig = px.scatter(
            data,
            x=x_col,
            y=y_col,
            title=title,
            hover_data=hover_data,
            color=plot_color_col,  # Use plot_color_col for coloring
            color_continuous_scale='viridis' if plot_color_col and pd.api.types.is_numeric_dtype(data[plot_color_col]) else None, # Apply continuous scale only if color_col is numeric
            color_discrete_sequence=self.color_palette if plot_color_col and not pd.api.types.is_numeric_dtype(data[plot_color_col]) else None, # Apply discrete scale if categorical
            size_max=15
        )
        
        if hover_col and hover_col in data.columns:
            fig.update_traces(
                # Ensure customdata indices are correct based on hover_data
                # If hover_data is [x_col, y_col, hover_col], then hover_col is index 2
                hovertemplate=f'<b>{hover_col}: %{{customdata[2]}}</b><br>' +
                              f'{x_col}: %{{x}}<br>' +
                              f'{y_col}: %{{y}}<extra></extra>'
            )
        
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            height=500
        )
        
        return fig

    
    def create_box_plot(self, data, y_col, x_col=None, title=None): # Added x_col parameter
        """
        Create a box plot
        """
        if title is None:
            if x_col:
                title = f"Distribution of {y_col} by {x_col}"
            else:
                title = f"Distribution of {y_col}"
        
        fig = px.box(
            data,
            y=y_col,
            x=x_col,  # Use the x_col parameter here
            title=title,
            color_discrete_sequence=['lightblue']
        )
        
        fig.update_layout(
            xaxis_title=x_col if x_col else "", # Set x-axis title if x_col is provided
            yaxis_title=y_col,
            height=500
        )
        
        return fig

    
    def create_histogram(self, data, col, bins=30, title=None):
        """
        Create a histogram
        """
        if title is None:
            title = f"Distribution of {col}"
        
        fig = px.histogram(
            data,
            x=col,
            nbins=bins,
            title=title,
            color_discrete_sequence=['lightcoral']
        )
        
        fig.update_layout(
            xaxis_title=col,
            yaxis_title='Frequency',
            height=500
        )
        
        return fig
    
    def create_correlation_heatmap(self, data, title=None):
        """
        Create a correlation heatmap for numeric columns
        """
        if title is None:
            title = "Correlation Matrix"
        
        # Select only numeric columns
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            return None
        
        # Calculate correlation matrix
        corr_matrix = numeric_data.corr()
        
        fig = px.imshow(
            corr_matrix,
            title=title,
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        
        fig.update_layout(
            height=500,
            width=500
        )
        
        return fig
    
    def create_multi_metric_chart(self, data, district_col, metric_cols, chart_type='bar'):
        """
        Create a chart with multiple metrics
        """
        if chart_type == 'bar':
            fig = go.Figure()
            
            for metric in metric_cols:
                fig.add_trace(go.Bar(
                    x=data[district_col],
                    y=data[metric],
                    name=metric,
                    hovertemplate=f'<b>District:</b> %{{x}}<br>' +
                                 f'<b>{metric}:</b> %{{y}}<br><extra></extra>'
                ))
            
            fig.update_layout(
                title="Multi-Metric Comparison by District",
                xaxis_title=district_col,
                yaxis_title="Value",
                height=500,
                barmode='group',
                xaxis_tickangle=-45
            )
            
        elif chart_type == 'line':
            fig = go.Figure()
            
            for metric in metric_cols:
                fig.add_trace(go.Scatter(
                    x=data[district_col],
                    y=data[metric],
                    mode='lines+markers',
                    name=metric,
                    hovertemplate=f'<b>District:</b> %{{x}}<br>' +
                                 f'<b>{metric}:</b> %{{y}}<br><extra></extra>'
                ))
            
            fig.update_layout(
                title="Multi-Metric Trends by District",
                xaxis_title=district_col,
                yaxis_title="Value",
                height=500,
                xaxis_tickangle=-45
            )
        
        return fig
    
    def create_ranking_chart(self, data, district_col, metric_col, top_n=10, ascending=False):
        """
        Create a ranking chart showing top/bottom N districts
        """
        # Sort data
        sorted_data = data.sort_values(metric_col, ascending=ascending)
        top_data = sorted_data.head(top_n)
        
        direction = "Bottom" if ascending else "Top"
        title = f"{direction} {top_n} Districts by {metric_col}"
        
        fig = px.bar(
            top_data,
            x=metric_col,
            y=district_col,
            orientation='h',
            title=title,
            color=metric_col,
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            height=max(400, top_n * 40),
            yaxis={'categoryorder': 'total ascending' if ascending else 'total descending'}
        )
        
        return fig
