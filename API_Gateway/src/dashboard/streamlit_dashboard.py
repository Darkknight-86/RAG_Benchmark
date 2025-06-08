"""
Streamlit Dashboard for Financial RAG Microservices Monitoring
Real-time visualization of metrics, service health, and performance
"""

import streamlit as st
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import asyncio
import websockets
import json
import time
from datetime import datetime, timedelta
import threading
import queue
import requests
from typing import Dict, List, Any

# Page config
st.set_page_config(
    page_title="Financial RAG Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global variables for real-time data
if 'metrics_data' not in st.session_state:
    st.session_state.metrics_data = {}
if 'service_health' not in st.session_state:
    st.session_state.service_health = {}
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'websocket_connected' not in st.session_state:
    st.session_state.websocket_connected = False

# Configuration
API_GATEWAY_HOST = "localhost"
API_GATEWAY_PORT = 8000
WEBSOCKET_URL = f"ws://{API_GATEWAY_HOST}:{API_GATEWAY_PORT}/ws/metrics"
METRICS_API_URL = f"http://{API_GATEWAY_HOST}:{API_GATEWAY_PORT}/metrics"

class DashboardMetrics:
    """Handle metrics collection and processing for dashboard"""

    @staticmethod
    def fetch_current_metrics() -> Dict[str, Any]:
        """Fetch current metrics from API Gateway"""
        try:
            response = requests.get(f"{METRICS_API_URL}/current", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch metrics: {response.status_code}")
                return {}
        except requests.exceptions.ConnectionError:
            st.warning("📡 Cannot connect to API Gateway - metrics may be limited")
            return {}
        except Exception as e:
            st.error(f"Error fetching metrics: {e}")
            return {}

    @staticmethod
    def process_metrics_for_charts(metrics: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Process metrics into DataFrames for plotting"""
        chart_data = {}

        if not metrics or 'metrics' not in metrics:
            return chart_data

        # Create time series data for each metric
        for metric_key, metric_data in metrics['metrics'].items():
            if isinstance(metric_data, dict) and 'avg' in metric_data:
                service, metric_type = metric_key.split('.', 1)

                if service not in chart_data:
                    chart_data[service] = []

                chart_data[service].append({
                    'metric': metric_type,
                    'avg': metric_data['avg'],
                    'min': metric_data['min'],
                    'max': metric_data['max'],
                    'count': metric_data['count'],
                    'latest': metric_data['latest']
                })

        # Convert to DataFrames
        for service in chart_data:
            chart_data[service] = pd.DataFrame(chart_data[service])

        return chart_data

def create_service_health_chart(health_data: Dict[str, Any]) -> go.Figure:
    """Create service health status chart"""
    if not health_data:
        return go.Figure()

    services = list(health_data.keys())
    statuses = [health_data[service]['status'] for service in services]

    # Color mapping
    colors = {
        'healthy': '#28a745',
        'unhealthy': '#dc3545',
        'unknown': '#6c757d'
    }

    fig = go.Figure(data=[
        go.Bar(
            x=services,
            y=[1] * len(services),
            marker_color=[colors.get(status, '#6c757d') for status in statuses],
            text=statuses,
            textposition='inside',
            hovertemplate='<b>%{x}</b><br>Status: %{text}<extra></extra>'
        )
    ])

    fig.update_layout(
        title="🏥 Service Health Status",
        xaxis_title="Services",
        yaxis_title="Status",
        showlegend=False,
        height=300,
        yaxis=dict(showticklabels=False)
    )

    return fig

def create_latency_chart(chart_data: Dict[str, pd.DataFrame]) -> go.Figure:
    """Create latency metrics chart"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('🔍 Vector Search Latency', '🧠 LLM Latency',
                       '⏱️ Total Query Time', '🗄️ Database Latency'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # Define metrics to show
    latency_metrics = {
        'vector_latency': (1, 1),
        'llm_latency': (1, 2),
        'total_time': (2, 1),
        'db_query_latency': (2, 2)
    }

    colors = px.colors.qualitative.Set3

    for service, df in chart_data.items():
        if df.empty:
            continue

        for i, (metric, (row, col)) in enumerate(latency_metrics.items()):
            metric_data = df[df['metric'] == metric]
            if not metric_data.empty:
                fig.add_trace(
                    go.Bar(
                        name=f"{service}",
                        x=[service],
                        y=metric_data['avg'].iloc[0:1],
                        marker_color=colors[i % len(colors)],
                        showlegend=(row == 1 and col == 1),
                        error_y=dict(
                            type='data',
                            array=[metric_data['max'].iloc[0] - metric_data['avg'].iloc[0]],
                            arrayminus=[metric_data['avg'].iloc[0] - metric_data['min'].iloc[0]]
                        )
                    ),
                    row=row, col=col
                )

    fig.update_layout(
        title="⚡ Latency Metrics (Average with Min/Max Range)",
        height=500
    )

    return fig

def create_throughput_chart(chart_data: Dict[str, pd.DataFrame]) -> go.Figure:
    """Create throughput metrics chart"""
    fig = go.Figure()

    colors = px.colors.qualitative.Pastel

    for i, (service, df) in enumerate(chart_data.items()):
        if df.empty:
            continue

        # Look for throughput metrics
        throughput_data = df[df['metric'].str.contains('throughput', case=False, na=False)]

        if not throughput_data.empty:
            fig.add_trace(
                go.Bar(
                    name=service.title(),
                    x=throughput_data['metric'],
                    y=throughput_data['avg'],
                    marker_color=colors[i % len(colors)],
                    text=throughput_data['avg'].round(2),
                    textposition='outside'
                )
            )

    fig.update_layout(
        title="🚀 Throughput Metrics (Items/Second)",
        xaxis_title="Metric Type",
        yaxis_title="Items per Second",
        height=400
    )

    return fig

def create_tokens_chart(chart_data: Dict[str, pd.DataFrame]) -> go.Figure:
    """Create token usage chart"""
    fig = go.Figure()

    for service, df in chart_data.items():
        if df.empty:
            continue

        tokens_data = df[df['metric'] == 'tokens_used']

        if not tokens_data.empty:
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=tokens_data['avg'].iloc[0],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': f"🎯 Average Tokens Used"},
                    gauge={
                        'axis': {'range': [0, 1000]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 200], 'color': "lightgray"},
                            {'range': [200, 500], 'color': "gray"},
                            {'range': [500, 1000], 'color': "lightcoral"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 800
                        }
                    }
                )
            )
            break  # Only show one gauge

    fig.update_layout(height=400)
    return fig

def main():
    """Main dashboard function"""
    st.title("📊 Financial RAG Microservices Dashboard")
    st.markdown("Real-time monitoring of streaming financial data, embeddings, and RAG queries")

    # Sidebar controls
    st.sidebar.header("🎛️ Dashboard Controls")
    auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 30, 5)
    time_window = st.sidebar.selectbox("Time Window", [1, 5, 15, 30], index=1)

    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now") or auto_refresh:
        # Fetch current metrics
        metrics_data = DashboardMetrics.fetch_current_metrics()
        st.session_state.metrics_data = metrics_data
        st.session_state.last_update = datetime.now()

    # Header metrics
    if st.session_state.last_update:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "🕐 Last Update",
                st.session_state.last_update.strftime("%H:%M:%S"),
                f"{time_window}min window"
            )

        with col2:
            metrics = st.session_state.metrics_data.get('summary', {})
            st.metric(
                "🏥 Services",
                f"{metrics.get('healthy_services', 0)}/{metrics.get('total_services', 0)}",
                "Healthy"
            )

        with col3:
            st.metric(
                "📊 Total Metrics",
                metrics.get('total_metrics', 0),
                "Collected"
            )

    # Main content
    if st.session_state.metrics_data:
        # Service health
        health_data = st.session_state.metrics_data.get('service_health', {})
        if health_data:
            st.plotly_chart(
                create_service_health_chart(health_data),
                use_container_width=True
            )

        # Process chart data
        chart_data = DashboardMetrics.process_metrics_for_charts(st.session_state.metrics_data)

        if chart_data:
            # Latency charts
            st.plotly_chart(
                create_latency_chart(chart_data),
                use_container_width=True
            )

            # Throughput and tokens
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(
                    create_throughput_chart(chart_data),
                    use_container_width=True
                )

            with col2:
                st.plotly_chart(
                    create_tokens_chart(chart_data),
                    use_container_width=True
                )

            # Raw metrics table
            with st.expander("📋 Raw Metrics Data"):
                for service, df in chart_data.items():
                    st.subheader(f"{service.title()} Service")
                    st.dataframe(df, use_container_width=True)

        # Export functionality
        st.sidebar.header("📤 Export")
        if st.sidebar.button("💾 Export CSV"):
            try:
                response = requests.post(f"{METRICS_API_URL}/export")
                if response.status_code == 200:
                    st.sidebar.success("✅ Metrics exported successfully!")
                else:
                    st.sidebar.error("❌ Export failed")
            except Exception as e:
                st.sidebar.error(f"❌ Export error: {e}")

    else:
        st.info("📡 No metrics data available. Make sure the API Gateway is running and services are active.")

        # Show connection status
        st.markdown("### 🔗 Connection Status")
        col1, col2 = st.columns(2)

        with col1:
            if DashboardMetrics.fetch_current_metrics():
                st.success("✅ API Gateway Connected")
            else:
                st.error("❌ API Gateway Disconnected")

        with col2:
            st.info("📊 Waiting for metrics data...")

    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()