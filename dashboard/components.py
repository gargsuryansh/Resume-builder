# Import Streamlit for building the web dashboard
import streamlit as st

# Import Plotly for interactive visualizations
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import Pandas for data handling
import pandas as pd

# Import datetime utilities (used for time-based analytics if needed)
from datetime import datetime, timedelta


# Class responsible for creating all dashboard UI components
class DashboardComponents:
    
    # Constructor to initialize color theme used across the dashboard
    def __init__(self, colors):
        self.colors = colors


    # Function to render a metric card (KPI) with optional trend indicator
    def render_metric_card(self, title, value, subtitle=None, trend=None, trend_value=None):
        """
        Displays a metric card showing key statistics such as total resumes,
        average ATS score, shortlisted candidates, etc.
        """

        # Initialize empty HTML for trend indicator
        trend_html = ""

        # If trend information is provided, show arrow and percentage
        if trend and trend_value:
            trend_color = self.colors['success'] if trend == 'up' else self.colors['danger']
            trend_arrow = '↑' if trend == 'up' else '↓'

            trend_html = f"""
                <div style="color: {trend_color}; font-size: 0.9rem; margin-top: 5px;">
                    {trend_arrow} {trend_value}%
                </div>
            """

        # Render the metric card using Streamlit markdown with HTML styling
        st.markdown(f"""
            <div class="metric-card">
                <div style="color: {self.colors['subtext']}; font-size: 0.9rem;">{title}</div>
                <div style="color: {self.colors['text']}; font-size: 2rem; font-weight: bold; margin: 10px 0;">
                    {value}
                </div>
                {f'<div style="color: {self.colors["subtext"]}; font-size: 0.8rem;">{subtitle}</div>' if subtitle else ''}
                {trend_html}
            </div>
        """, unsafe_allow_html=True)


    # Function to create a gauge chart (used for ATS score visualization)
    def create_gauge_chart(self, value, title):
        """
        Creates a gauge chart to represent percentage-based metrics
        such as ATS score or matching confidence.
        """

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': title, 'font': {'size': 24, 'color': self.colors['text']}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': self.colors['text']},
                'bar': {'color': self.colors['primary']},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",

                # Color-coded ranges for better interpretation
                'steps': [
                    {'range': [0, 40], 'color': self.colors['danger']},
                    {'range': [40, 70], 'color': self.colors['warning']},
                    {'range': [70, 100], 'color': self.colors['success']}
                ],
            }
        ))

        # Layout styling for the gauge chart
        fig.update_layout(
            paper_bgcolor=self.colors['card'],
            plot_bgcolor=self.colors['card'],
            font={'color': self.colors['text']},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )

        return fig


    # Function to create a line chart for trend analysis
    def create_trend_chart(self, dates, values, title):
        """
        Creates a line chart to visualize trends over time,
        such as resume uploads or average ATS score per day.
        """

        fig = go.Figure()

        # Add line + marker plot
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            line=dict(color=self.colors['info'], width=3),
            marker=dict(size=8, color=self.colors['info'])
        ))

        # Layout configuration
        fig.update_layout(
            title=title,
            paper_bgcolor=self.colors['card'],
            plot_bgcolor=self.colors['card'],
            font={'color': self.colors['text']},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.colors['background']
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.colors['background']
            )
        )

        return fig


    # Function to create a bar chart for categorical data
    def create_bar_chart(self, categories, values, title):
        """
        Creates a bar chart to compare values across categories,
        such as skill-wise match count or resume distribution.
        """

        fig = go.Figure(go.Bar(
            x=categories,
            y=values,
            marker_color=self.colors['primary'],
            text=values,
            textposition='auto',
        ))

        # Layout styling
        fig.update_layout(
            title=title,
            paper_bgcolor=self.colors['card'],
            plot_bgcolor=self.colors['card'],
            font={'color': self.colors['text']},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis=dict(
                showgrid=False,
                title_text="Categories",
                color=self.colors['text']
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.colors['background'],
                title_text="Values",
                color=self.colors['text']
            )
        )

        return fig


    # Function to create a dual-axis chart
    def create_dual_axis_chart(self, categories, values1, values2, title):
        """
        Creates a dual-axis chart where:
        - Bar chart shows count
        - Line chart shows score
        Useful for comparing two metrics together.
        """

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Bar chart (primary y-axis)
        fig.add_trace(
            go.Bar(
                x=categories,
                y=values1,
                name="Count",
                marker_color=self.colors['secondary']
            ),
            secondary_y=False
        )

        # Line chart (secondary y-axis)
        fig.add_trace(
            go.Scatter(
                x=categories,
                y=values2,
                name="Score",
                line=dict(color=self.colors['warning'], width=3),
                mode='lines+markers'
            ),
            secondary_y=True
        )

        # Layout configuration
        fig.update_layout(
            title=title,
            paper_bgcolor=self.colors['card'],
            plot_bgcolor=self.colors['card'],
            font={'color': self.colors['text']},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # Axis labels
        fig.update_xaxes(title_text="Categories", color=self.colors['text'])
        fig.update_yaxes(title_text="Count", color=self.colors['text'], secondary_y=False)
        fig.update_yaxes(title_text="Score", color=self.colors['text'], secondary_y=True)

        return fig
