"""
Financial RAG Dashboard - LLM Query Testing Interface
Focus on LLM query testing with simplified metrics (streaming data exports to CSV automatically)
"""

import streamlit as st
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any

# Configure page with wide layout and clean styling
st.set_page_config(
    page_title="Financial RAG Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }

    .status-success {
        border-left-color: #28a745 !important;
    }

    .status-warning {
        border-left-color: #ffc107 !important;
    }

    .status-error {
        border-left-color: #dc3545 !important;
    }

    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #333;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
    }

    .query-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }

    .export-section {
        background: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }

    .stButton button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    .metric-big {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
    }

    .metric-label {
        font-size: 1.1rem;
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Global state management
if 'metrics_data' not in st.session_state:
    st.session_state.metrics_data = {}
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Configuration
API_GATEWAY_HOST = "localhost"
API_GATEWAY_PORT = 8000
METRICS_API_URL = f"http://{API_GATEWAY_HOST}:{API_GATEWAY_PORT}/metrics"
QUERY_API_URL = f"http://{API_GATEWAY_HOST}:{API_GATEWAY_PORT}/api"

class ModernDashboard:
    """Enhanced dashboard with modern design and LLM query functionality"""

    @staticmethod
    def fetch_current_metrics() -> Dict[str, Any]:
        """Fetch current metrics from FastAPI Gateway"""
        try:
            response = requests.get(f"{METRICS_API_URL}/current", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"❌ Failed to fetch metrics: HTTP {response.status_code}")
                return {}
        except requests.exceptions.ConnectionError:
            st.warning("🔌 Cannot connect to FastAPI Gateway - Please ensure it's running on port 8000")
            return {}
        except Exception as e:
            st.error(f"❌ Error fetching metrics: {e}")
            return {}

    @staticmethod
    def test_llm_query(query: str, ticker: str = None, model: str = "google/flan-t5-small", temperature: float = 0.7):
        """Test LLM query functionality"""
        try:
            if ticker and ticker != "General Query":
                # Financial-specific query
                payload = {
                    "query": query,
                    "ticker": ticker,
                    "model_name": model,
                    "temperature": temperature
                }
                endpoint = f"{QUERY_API_URL}/financial/query"
            else:
                # General query
                payload = {
                    "query": query,
                    "model_name": model,
                    "temperature": temperature,
                    "top_k": 5,
                    "max_tokens": 200
                }
                endpoint = f"{QUERY_API_URL}/query"

            response = requests.post(endpoint, json=payload, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def export_csv(export_type: str, minutes: int = 60):
        """Export metrics to CSV"""
        try:
            payload = {"export_type": export_type, "minutes": minutes}
            response = requests.post(f"{METRICS_API_URL}/export", json=payload, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Export failed: HTTP {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

def render_header():
    """Render the main header section"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Financial RAG Intelligence Dashboard</h1>
        <p style="font-size: 1.2rem; margin-top: 1rem;">
            Real-time Analytics • LLM Query Testing • Dual Metrics System
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_key_metrics(metrics_data: Dict[str, Any]):
    """Render key metrics in a prominent display"""
    if not metrics_data:
        st.warning("📊 No metrics data available")
        return

    st.markdown('<div class="section-header">🎯 Key Performance Indicators</div>', unsafe_allow_html=True)

    # Extract key metrics
    streaming_data = metrics_data.get('streaming_pipeline_metrics', {})
    real_time = streaming_data.get('real_time', {})
    summary = metrics_data.get('summary', {})

    # Create 5 columns for key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("""
        <div class="metric-card status-success">
            <div class="metric-big">{}</div>
            <div class="metric-label">VD Load Time (ms)</div>
            <small>KEY METRIC - Vector Database Performance</small>
        </div>
        """.format(f"{real_time.get('avg_database_latency_ms', 0):.1f}"), unsafe_allow_html=True)

    with col2:
        ingestion_rate = real_time.get('ingestion_rate_per_second', 0)
        status_class = "status-success" if ingestion_rate > 0 else "status-warning"
        st.markdown("""
        <div class="metric-card {}">
            <div class="metric-big">{:.1f}</div>
            <div class="metric-label">Data Ingestion Rate</div>
            <small>Records per second</small>
        </div>
        """.format(status_class, ingestion_rate), unsafe_allow_html=True)

    with col3:
        active_tickers = real_time.get('active_tickers', 0)
        st.markdown("""
        <div class="metric-card status-success">
            <div class="metric-big">{}</div>
            <div class="metric-label">Active Tickers</div>
            <small>Live streaming symbols</small>
        </div>
        """.format(active_tickers), unsafe_allow_html=True)

    with col4:
        healthy_services = summary.get('healthy_services', 0)
        total_services = summary.get('total_services', 4)
        status_class = "status-success" if healthy_services == total_services else "status-warning"
        st.markdown("""
        <div class="metric-card {}">
            <div class="metric-big">{}/{}</div>
            <div class="metric-label">Service Health</div>
            <small>Microservices online</small>
        </div>
        """.format(status_class, healthy_services, total_services), unsafe_allow_html=True)

    with col5:
        embedding_latency = real_time.get('avg_embedding_latency_ms', 0)
        status_class = "status-success" if embedding_latency < 500 else "status-warning"
        st.markdown("""
        <div class="metric-card {}">
            <div class="metric-big">{:.0f}</div>
            <div class="metric-label">Embedding Latency</div>
            <small>Average processing time (ms)</small>
        </div>
        """.format(status_class, embedding_latency), unsafe_allow_html=True)

def render_llm_query_interface():
    """Render the LLM query testing interface"""
    st.markdown('<div class="section-header">🧠 LLM Query Testing</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="query-section">
        <h3>💬 Test Financial RAG Queries</h3>
        <p>Query the live financial data using natural language. The system will search through
        streaming financial data and provide intelligent responses powered by the RAG pipeline.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Query input
        query_text = st.text_area(
            "Enter your financial question:",
            placeholder="Example: What is the recent performance of Amazon stock? How is Coles Group performing?",
            height=100,
            help="Ask questions about any financial ticker or general market analysis"
        )

        # Query options
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            ticker_options = ["General Query", "AMZN", "COL.AX", "JBH.AX", "WOW.AX", "QAN.AX", "TLS.AX", "GOOGL"]
            selected_ticker = st.selectbox("Focus on specific ticker (optional):", ticker_options)

        with col_b:
            model_options = ["google/flan-t5-small", "google/flan-t5-base", "microsoft/DialoGPT-medium"]
            selected_model = st.selectbox("Model:", model_options)

        with col_c:
            temperature = st.slider("Response creativity:", 0.0, 1.0, 0.7, 0.1)

    with col2:
        st.markdown("### 📋 Quick Examples")
        example_queries = [
            "What's the current market sentiment for tech stocks?",
            "How has WOW.AX been performing recently?",
            "Compare Amazon and Google stock performance",
            "What are the key financial metrics for Australian banks?",
            "Analyze the retail sector trends"
        ]

        for i, example in enumerate(example_queries):
            if st.button(f"📝 Example {i+1}", key=f"example_{i}", help=example):
                st.session_state['query_input'] = example

    # Query execution
    col_query, col_clear = st.columns([3, 1])

    with col_query:
        if st.button("🚀 Execute Query", type="primary", disabled=not query_text.strip()):
            with st.spinner("🔍 Processing your query through the RAG pipeline..."):
                ticker = selected_ticker if selected_ticker != "General Query" else None
                result = ModernDashboard.test_llm_query(query_text, ticker, selected_model, temperature)

                if "error" in result:
                    st.error(f"❌ Query failed: {result['error']}")
                else:
                    # Store in history
                    st.session_state.query_history.insert(0, {
                        "timestamp": datetime.now(),
                        "query": query_text,
                        "ticker": ticker,
                        "model": selected_model,
                        "result": result
                    })

                    # Display results
                    render_query_results(result)

    with col_clear:
        if st.button("🗑️ Clear History"):
            st.session_state.query_history = []
            st.success("Query history cleared!")

def render_query_results(result: Dict[str, Any]):
    """Render query results in an attractive format"""
    st.markdown("---")
    st.markdown("### 📝 Query Results")

    # Response
    if "response" in result:
        st.markdown("#### 🎯 AI Response")
        st.markdown(f"""
        <div style="background: #f0f8ff; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #4CAF50;">
            <p style="font-size: 1.1rem; line-height: 1.6; margin: 0;">{result['response']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Metrics
    if "metrics" in result:
        st.markdown("#### ⚡ Performance Metrics")
        metrics = result["metrics"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Vector Search", f"{metrics.get('vector_latency', 0):.0f}ms", "Retrieval time")
        with col2:
            st.metric("LLM Generation", f"{metrics.get('llm_latency', 0):.0f}ms", "Response time")
        with col3:
            st.metric("Total Time", f"{metrics.get('total_time', 0):.2f}s", "End-to-end")
        with col4:
            st.metric("Tokens Used", f"{metrics.get('tokens_used', 0)}", f"Model: {metrics.get('model_name', 'Unknown')}")

    # Sources
    if "sources" in result and result["sources"]:
        st.markdown("#### 📚 Knowledge Sources")
        for i, source in enumerate(result["sources"][:3]):  # Show top 3 sources
            with st.expander(f"Source {i+1} (Relevance: {source.get('score', 0):.2f})"):
                st.text(source.get('content', 'No content available'))
                if 'metadata' in source:
                    st.json(source['metadata'])

def render_query_history():
    """Render query history"""
    if not st.session_state.query_history:
        return

    st.markdown("#### 📚 Recent Query History")

    for i, query_item in enumerate(st.session_state.query_history[:5]):  # Show last 5
        with st.expander(f"🕐 {query_item['timestamp'].strftime('%H:%M:%S')} - {query_item['query'][:50]}..."):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Query:** {query_item['query']}")
                if 'result' in query_item and 'response' in query_item['result']:
                    st.write(f"**Response:** {query_item['result']['response']}")

            with col2:
                st.write(f"**Ticker:** {query_item['ticker'] or 'General'}")
                st.write(f"**Model:** {query_item['model']}")
                if 'result' in query_item and 'metrics' in query_item['result']:
                    metrics = query_item['result']['metrics']
                    st.write(f"**Time:** {metrics.get('total_time', 0):.2f}s")

# Removed render_streaming_charts function - streaming metrics now export directly to CSV

def render_export_section():
    """Render CSV export functionality"""
    st.markdown('<div class="section-header">📤 Data Export</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="export-section">
        <h3>💾 Export Metrics to CSV</h3>
        <p>Download historical metrics data for analysis and reporting. Choose between streaming
        pipeline metrics (live data flow) or RAG query metrics (LLM performance).</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        export_type = st.selectbox(
            "Export Type:",
            ["streaming", "queries"],
            format_func=lambda x: {
                "streaming": "📊 Streaming Pipeline Metrics (VD load times, ingestion rates)",
                "queries": "🧠 RAG Query Metrics (LLM performance, response times)"
            }[x]
        )

    with col2:
        time_range = st.selectbox(
            "Time Range:",
            [60, 180, 360, 720, 1440],
            format_func=lambda x: f"{x} minutes" if x < 1440 else "24 hours",
            index=1
        )

    with col3:
        if st.button("📥 Export CSV", type="primary"):
            with st.spinner("Generating CSV export..."):
                result = ModernDashboard.export_csv(export_type, time_range)

                if "error" in result:
                    st.error(f"❌ Export failed: {result['error']}")
                else:
                    st.success(f"✅ Export successful!")
                    st.json(result)

def render_sidebar():
    """Render enhanced sidebar with controls"""
    with st.sidebar:
        st.markdown("## 🎛️ Dashboard Controls")

        # Auto-refresh controls
        st.markdown("### 🔄 Real-time Updates")
        auto_refresh = st.checkbox("Enable auto-refresh", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 15)

        # Manual refresh
        if st.button("🔄 Refresh Now", type="primary"):
            st.rerun()

        # Connection status
        st.markdown("### 🔗 Connection Status")
        try:
            response = requests.get(f"http://{API_GATEWAY_HOST}:{API_GATEWAY_PORT}/api/health", timeout=3)
            if response.status_code == 200:
                st.success("✅ FastAPI Gateway Connected")
                health_data = response.json()
                if "services" in health_data:
                    for service, status in health_data["services"].items():
                        if status == "healthy":
                            st.success(f"✅ {service.replace('_', ' ').title()}")
                        else:
                            st.error(f"❌ {service.replace('_', ' ').title()}")
            else:
                st.error("❌ Gateway Connection Failed")
        except:
            st.error("❌ Cannot reach API Gateway")

        # Quick stats
        if st.session_state.metrics_data:
            st.markdown("### 📊 Quick Stats")
            metrics_data = st.session_state.metrics_data
            streaming_data = metrics_data.get('streaming_pipeline_metrics', {})
            real_time = streaming_data.get('real_time', {})

            st.metric("VD Load Time", f"{real_time.get('avg_database_latency_ms', 0):.1f}ms")
            st.metric("Active Tickers", f"{real_time.get('active_tickers', 0)}")
            st.metric("Query History", f"{len(st.session_state.query_history)}")

        # System info
        st.markdown("### ℹ️ System Information")
        st.info(f"**Dashboard Version:** 2.0.0 Redesigned\n**Update Time:** {datetime.now().strftime('%H:%M:%S')}")

        return auto_refresh, refresh_interval

def main():
    """Main dashboard application"""
    render_header()

    # Sidebar controls
    auto_refresh, refresh_interval = render_sidebar()

    # Fetch metrics data
    if auto_refresh or 'metrics_data' not in st.session_state or not st.session_state.metrics_data:
        metrics_data = ModernDashboard.fetch_current_metrics()
        st.session_state.metrics_data = metrics_data
        st.session_state.last_update = datetime.now()
    else:
        metrics_data = st.session_state.metrics_data

    # Render main sections
    if metrics_data:
        render_key_metrics(metrics_data)

        # Add spacing
        st.markdown("<br>", unsafe_allow_html=True)

        render_llm_query_interface()
        render_query_history()

        st.markdown("<br>", unsafe_allow_html=True)

        # Removed streaming charts - dashboard now focuses on LLM query testing
        st.markdown("""
        <div style="background: #e8f4fd; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #2196F3;">
            <h3>📊 Streaming Data Note</h3>
            <p>Live streaming metrics (VD load times, ingestion rates, active tickers) are automatically exported to CSV files every 5 minutes.</p>
            <p><strong>📁 Check for files:</strong> <code>live_streaming_metrics_YYYYMMDD_HHMMSS.csv</code></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        render_export_section()

        # Debug section (collapsible)
        with st.expander("🔧 Debug Information"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Streaming Pipeline Data:**")
                st.json(metrics_data.get('streaming_pipeline_metrics', {}))
            with col2:
                st.markdown("**RAG Query Data:**")
                st.json(metrics_data.get('rag_query_metrics', {}))

    else:
        st.error("❌ No metrics data available")
        st.markdown("""
        ### 🛠️ Troubleshooting
        1. **Check FastAPI Gateway:** Ensure it's running on port 8000
        2. **Check Services:** Verify Embeddings and LLM services are active
        3. **Check Network:** Ensure dashboard can reach API endpoints

        **Quick Start:**
        ```bash
        # In terminal 1: Start FastAPI Gateway
        cd API_Gateway && poetry run uvicorn api_gateway.fastapi_server:app --host 0.0.0.0 --port 8000

        # In terminal 2: Start streaming service
        make start-streaming
        ```
        """)

    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()