"""
Financial RAG Dashboard - LLM Query Testing Interface
Focus on LLM query testing with simplified metrics (streaming data exports to CSV automatically)
"""

import streamlit as st
import json
import time
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any
import logging
import pandas as pd
import os
import io

# Demo mode detection
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure page with wide layout and clean styling
st.set_page_config(
    page_title="🚀 RAG System Enterprise Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling and readability
st.markdown("""
<style>
    /* Stunning main header with perfect readability */
    .main-header {
        text-align: center;
        padding: 2.5rem 0;
        background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 50%, #581c87 100%);
        color: white;
        border-radius: 18px;
        margin-bottom: 2rem;
        box-shadow: 0 6px 25px rgba(30, 58, 138, 0.4);
        border: 2px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
        animation: shine 3s infinite;
    }

    @keyframes shine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    /* Make the "Powered by" text black for readability */
    .main-header p {
        color: #1a1a1a !important;
        font-weight: bold !important;
        background: rgba(255, 255, 255, 0.9) !important;
        padding: 0.5rem 1rem !important;
        border-radius: 8px !important;
        display: inline-block !important;
        margin-top: 1rem !important;
    }

    /* Beautiful section headers with excellent readability and color bubbles */
    .section-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: #ffffff;
        border: none;
        padding: 1.5rem 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        font-size: 1.4rem;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 20px rgba(30, 58, 138, 0.4);
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        position: relative;
        border: 2px solid rgba(255, 255, 255, 0.2);
    }

    .section-header::before {
        content: '';
        position: absolute;
        left: 15px;
        top: 50%;
        transform: translateY(-50%);
        width: 12px;
        height: 12px;
        background: #4ade80;
        border-radius: 50%;
        box-shadow: 0 0 10px rgba(74, 222, 128, 0.6);
    }

    /* Connection status headers with color bubbles */
    .status-header {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: #ffffff;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-size: 1.1rem;
        font-weight: bold;
        box-shadow: 0 3px 15px rgba(5, 150, 105, 0.3);
        position: relative;
        border: 2px solid rgba(255, 255, 255, 0.2);
    }

    .status-header::before {
        content: '';
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        width: 10px;
        height: 10px;
        background: #fbbf24;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(251, 191, 36, 0.8);
    }

    /* System info headers with color bubbles */
    .info-header {
        background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 100%);
        color: #ffffff;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-size: 1.1rem;
        font-weight: bold;
        box-shadow: 0 3px 15px rgba(124, 58, 237, 0.3);
        position: relative;
        border: 2px solid rgba(255, 255, 255, 0.2);
    }

    .info-header::before {
        content: '';
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        width: 10px;
        height: 10px;
        background: #06b6d4;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(6, 182, 212, 0.8);
    }

    /* Query section headers with color bubbles */
    .query-header {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        color: #ffffff;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-size: 1.2rem;
        font-weight: bold;
        box-shadow: 0 3px 15px rgba(220, 38, 38, 0.3);
        position: relative;
        border: 2px solid rgba(255, 255, 255, 0.2);
    }

    .query-header::before {
        content: '';
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        width: 10px;
        height: 10px;
        background: #f59e0b;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(245, 158, 11, 0.8);
    }

    /* Query section with better contrast */
    .query-section {
        background: #ffffff;
        border: 2px solid #e0e0e0;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 2px 15px rgba(0,0,0,0.08);
    }

    /* Query section headers and text should be black */
    .query-section h3 {
        color: #1a1a1a !important;
        font-weight: bold !important;
    }

    .query-section p {
        color: #374151 !important;
    }

    /* Export section with better readability */
    .export-section {
        background: #f8f9fa;
        border: 2px solid #dee2e6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #1a1a1a !important;
    }

    .export-section h3 {
        color: #1a1a1a !important;
        font-weight: bold !important;
    }

    /* Beautiful button styling with excellent readability */
    .stButton button {
        background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(30, 64, 175, 0.3);
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }

    .stButton button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30, 64, 175, 0.4);
    }

    /* Primary button styling */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        box-shadow: 0 3px 10px rgba(220, 38, 38, 0.3);
    }

    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
        box-shadow: 0 5px 15px rgba(220, 38, 38, 0.4);
    }

    /* Better metric cards */
    .metric-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
    }

    /* Status indicators with better contrast */
    .status-success {
        color: #2e7d32 !important;
        background-color: #e8f5e8 !important;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #4CAF50 !important;
    }

    .status-warning {
        color: #f57c00 !important;
        background-color: #fff3e0 !important;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #ff9800 !important;
    }

    .status-error {
        color: #c62828 !important;
        background-color: #ffebee !important;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #f44336 !important;
    }

    /* ENHANCED TEXT READABILITY - ALL TEXT VERY DARK */
    .stMarkdown {
        color: #1a1a1a !important;
    }

    /* All headers - very dark with excellent readability */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #1a1a1a !important;
        font-weight: bold !important;
        text-shadow: none !important;
    }

    /* All paragraph text - dark gray for excellent readability */
    .stMarkdown p {
        color: #2d3748 !important;
        font-weight: 500 !important;
    }

    /* Section headers - extra dark */
    .stMarkdown h3 {
        color: #1a1a1a !important;
        font-weight: bold !important;
        font-size: 1.3rem !important;
    }

    .stMarkdown h4 {
        color: #1a1a1a !important;
        font-weight: bold !important;
    }

    /* Tips and information text - dark */
    .stMarkdown em {
        color: #374151 !important;
    }

    /* Code text - very dark */
    .stMarkdown code {
        color: #1a1a1a !important;
        background-color: #f3f4f6 !important;
    }

    /* ALL TEXT AND HEADINGS - VERY DARK FOR MAXIMUM READABILITY */

    /* Widget labels - dark for readability */
    label[data-testid="stWidgetLabel"] {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }

    /* Text area labels - dark */
    .stTextArea label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }

    /* Selectbox labels - dark */
    .stSelectbox label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }

    /* Slider labels - dark */
    .stSlider label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }

    /* All widget labels - dark */
    .stApp label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }

    /* Caption text - dark */
    .stMarkdown .caption {
        color: #2d3748 !important;
    }

    /* All section headers - very dark */
    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h4,
    div[data-testid="stMarkdownContainer"] h5,
    div[data-testid="stMarkdownContainer"] h6 {
        color: #1a1a1a !important;
        font-weight: bold !important;
    }

    /* All subheader elements - very dark */
    .element-container .stMarkdown h1,
    .element-container .stMarkdown h2,
    .element-container .stMarkdown h3,
    .element-container .stMarkdown h4,
    .element-container .stMarkdown h5,
    .element-container .stMarkdown h6 {
        color: #1a1a1a !important;
        font-weight: bold !important;
    }

    /* Main content headers - very dark */
    .main .stMarkdown h1,
    .main .stMarkdown h2,
    .main .stMarkdown h3,
    .main .stMarkdown h4,
    .main .stMarkdown h5,
    .main .stMarkdown h6 {
        color: #1a1a1a !important;
        font-weight: bold !important;
    }

    /* All paragraph text - dark */
    .stMarkdown p {
        color: #2d3748 !important;
        font-weight: 500 !important;
    }

    /* List items - dark */
    .stMarkdown li {
        color: #2d3748 !important;
    }

    /* Strong/bold text - very dark */
    .stMarkdown strong {
        color: #1a1a1a !important;
        font-weight: bold !important;
    }

    /* Improved sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
    }

    /* Better contrast for metrics */
    .metric-big {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2196F3;
    }

    .metric-label {
        font-size: 1.1rem;
        color: #555555;
        margin-top: 0.5rem;
    }

    /* Improved text areas and inputs */
    .stTextArea textarea {
        border: 2px solid #dee2e6 !important;
        border-radius: 8px !important;
        background-color: #ffffff !important;
        color: #212529 !important;
        font-size: 16px !important;
    }

    .stTextArea textarea:focus {
        border-color: #28a745 !important;
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
        outline: none !important;
    }

    /* Improve selectbox readability */
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #212529 !important;
        border: 2px solid #dee2e6 !important;
    }

    /* Better expander styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
    }

    /* Info boxes with better contrast */
    .stInfo {
        background-color: #e3f2fd;
        border: 1px solid #2196F3;
        color: #1565c0;
    }

    .stSuccess {
        background-color: #e8f5e8;
        border: 1px solid #4CAF50;
        color: #2e7d32;
    }

    .stWarning {
        background-color: #fff3e0;
        border: 1px solid #ff9800;
        color: #f57c00;
    }

    .stError {
        background-color: #ffebee;
        border: 1px solid #f44336;
        color: #c62828;
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
if 'selected_query' not in st.session_state:
    st.session_state.selected_query = ''
if 'last_query_result' not in st.session_state:
    st.session_state.last_query_result = None

# Configuration
API_GATEWAY_HOST = "localhost"
API_GATEWAY_PORT = 8000
METRICS_API_URL = f"http://{API_GATEWAY_HOST}:{API_GATEWAY_PORT}/metrics"
QUERY_API_URL = f"http://{API_GATEWAY_HOST}:{API_GATEWAY_PORT}/api"

class ModernDashboard:
    """Enhanced dashboard with modern design and LLM query functionality"""

    @staticmethod
    def load_csv_file(file_path: str) -> pd.DataFrame:
        """Load CSV file and return as DataFrame"""
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_available_metrics_files() -> Dict[str, str]:
        """Get available metrics CSV files"""
        if DEMO_MODE:
            # Demo mode uses sample data
            base_paths = ["sample_data"]
        else:
            # Production mode paths
            # For Docker/Render deployment, files are in /app/API_Gateway_Data/
            # For local development, files are in API_Gateway/Data/
            base_paths = [
                "/app/API_Gateway_Data",  # Docker/Render path
            "API_Gateway/Data",       # Local development path
            "../API_Gateway/Data",    # Alternative local path
            "../../API_Gateway/Data"  # Alternative path from embeddings service
        ]

        files = {}

        for base_path in base_paths:
            if os.path.exists(base_path):
                # Streaming metrics
                streaming_path = os.path.join(base_path, "streaming_metrics")
                if os.path.exists(streaming_path):
                    for metric_type in ["streaming_data", "chunking", "embedding", "vector_db"]:
                        file_path = os.path.join(streaming_path, f"{metric_type}_metrics.csv")
                        if os.path.exists(file_path):
                            files[f"{metric_type}_metrics"] = file_path

                # Query metrics
                query_path = os.path.join(base_path, "query_metrics")
                if os.path.exists(query_path):
                    for file_name in os.listdir(query_path):
                        if file_name.endswith('.csv'):
                            files[file_name.replace('.csv', '')] = os.path.join(query_path, file_name)
                break

        return files

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
    def test_llm_query(query: str, ticker: str = None, model: str = "meta-llama/Llama-3.2-1B-Instruct", temperature: float = 0.7):
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
                    "max_tokens": 1000
                }
                endpoint = f"{QUERY_API_URL}/query"

            response = requests.post(endpoint, json=payload, timeout=240)

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}

        except requests.exceptions.Timeout:
            return {"error": "Request timeout (240s) - LLM processing took too long. Consider using a simpler query or shorter context."}
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
    if DEMO_MODE:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center; color: white; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
            <h1 style="margin: 0; font-size: 2.5rem;">🚀 RAG Benchmarking Platform</h1>
            <h2 style="margin: 0.5rem 0; font-size: 1.5rem; opacity: 0.9;">✨ LIVE DEMO - Sample Data Showcase</h2>
                         <div style="background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 10px; margin: 1.5rem 0;">
                 <p style="font-size: 1.2rem; margin: 0.5rem 0;"><strong>🎯 12,000+ Line Enterprise RAG System</strong></p>
                 <p style="font-size: 1.1rem; margin: 0.5rem 0;">🏗️ <strong>Architecture:</strong> 3 Microservices • gRPC Communication • Protocol Buffers</p>
                 <p style="font-size: 1.1rem; margin: 0.5rem 0;">🤖 <strong>AI/ML Stack:</strong> HuggingFace Transformers • PyTorch MPS • LangChain RAG</p>
                 <p style="font-size: 1.1rem; margin: 0.5rem 0;">⚡ <strong>Performance:</strong> Async Streaming • Vector DB • Apple Silicon GPU (10x faster)</p>
                 <p style="font-size: 1.1rem; margin: 0.5rem 0;">🛠️ <strong>DevOps:</strong> FastAPI • Docker Multi-stage • Poetry • ClickHouse Cloud</p>
             </div>
            <div style="margin-top: 1.5rem;">
                <a href="https://github.com/Darkknight-86/RAG_Benchmark" target="_blank" style="background: #28a745; color: white; padding: 12px 30px; border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 1.1rem; margin: 0 10px; display: inline-block;">
                    📂 Fork Repository
                </a>
                <a href="https://github.com/Darkknight-86/RAG_Benchmark#-quick-start" target="_blank" style="background: #17a2b8; color: white; padding: 12px 30px; border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 1.1rem; margin: 0 10px; display: inline-block;">
                    🚀 Setup Guide
                </a>
            </div>
            <p style="margin-top: 1rem; font-size: 0.95rem; opacity: 0.8;">
                👆 <strong>Try the downloads below!</strong> • This demo shows real sample data from the production system
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-header">
        <h1>🚀 RAG System Dashboard</h1>
        <p><strong>Powered by:</strong> Llama 3.2 1B • ClickHouse Vector DB • Yahoo Live Trading Data</p>
    </div>
    """, unsafe_allow_html=True)

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

    # Query options
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        ticker_options = [
            "General Query",
            # Major Cryptocurrencies
            "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "ADA-USD", "XRP-USD", "DOGE-USD",
            "AVAX-USD", "DOT-USD", "LINK-USD", "MATIC-USD", "LTC-USD",
            # US Stocks
            "AMZN", "GOOGL", "AAPL", "MSFT", "META",
            # Australian Stocks
            "COL.AX", "JBH.AX", "WOW.AX", "QAN.AX", "TLS.AX"
        ]
        selected_ticker = st.selectbox("Focus on specific ticker (optional):", ticker_options)

    with col_b:
        model_options = ["meta-llama/Llama-3.2-1B-Instruct", "meta-llama/Llama-3.2-3B-Instruct"]
        selected_model = st.selectbox("Model:", model_options)

    with col_c:
        temperature = st.slider("Response creativity:", 0.0, 1.0, 0.7, 0.1)

    # Query input section
    col1, col2 = st.columns([1.2, 1])

    with col1:
        # Query input with improved styling
        query_text = st.text_area(
            "✨ Enter your financial question:",
            value=st.session_state.get('selected_query', ''),
            placeholder="💡 Example: What is Bitcoin's current price and trend? How is Ethereum performing vs Bitcoin?",
            height=120,
            help="🎯 Ask questions about cryptocurrency or financial market analysis. Our AI will search through live financial data and provide intelligent responses.",
            key="main_query_input"
        )

        # Clear query button
        if st.button("🗑️ Clear Query", key="clear_query_btn", help="Clear the text box"):
            st.session_state['selected_query'] = ''
            st.rerun()

    with col2:
        # Removed query suggestions section as requested
        st.markdown("### 💡 Tips")
        st.info("💡 **Try asking about:**\n- Bitcoin or crypto prices\n- Market trends\n- Stock comparisons\n- Financial analysis")

    # Query execution
    col_query, col_clear = st.columns([3, 1])

    with col_query:
        if DEMO_MODE:
            if st.button("🚀 Execute Query", type="primary", disabled=not query_text.strip()):
                st.info("🎯 **Demo Mode**: This is a preview of the dashboard interface. Fork the repository to run live queries with the full RAG pipeline!")
                st.markdown("""
                **📊 In the full system, this would:**
                - 🔍 Search through live financial data in ClickHouse
                - 🧠 Process your query with Llama 3.2 LLM
                - 📈 Return intelligent financial analysis
                - ⚡ Show real-time performance metrics
                """)
        else:
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

    # Enhanced Metrics focusing on retrieval quality
    if "metrics" in result:
        st.markdown("#### 🎯 Retrieval Quality & Response Analysis")
        metrics = result["metrics"]

        # Primary metrics focused on VD → LLM pipeline quality
        col1, col2, col3 = st.columns(3)

        with col1:
            vd_latency = metrics.get('vector_latency', 0) * 1000  # Convert to ms
            vd_quality = "🟢 Excellent" if vd_latency < 100 else "🟡 Good" if vd_latency < 200 else "🔴 Needs Attention"
            st.metric("Vector DB Retrieval", f"{vd_latency:.0f}ms", vd_quality)

        with col2:
            llm_latency = metrics.get('llm_latency', 0)
            response_quality = "🎯 Rich Context" if metrics.get('tokens_used', 0) > 50 else "⚠️ Limited Context"
            st.metric("LLM Processing", f"{llm_latency:.2f}s", response_quality)

        with col3:
            tokens = metrics.get('tokens_used', 0)
            token_indicator = "📝 Detailed" if tokens > 60 else "📄 Standard" if tokens > 30 else "📋 Brief"
            st.metric("Response Depth", f"{tokens} tokens", token_indicator)

        # Sources quality analysis
        if "sources" in result and result["sources"]:
            st.markdown("#### 📊 Vector Database Retrieval Analysis")

            sources = result["sources"]
            if sources:
                avg_score = sum(source.get('score', 0) for source in sources) / len(sources)
                high_quality_sources = len([s for s in sources if s.get('score', 0) > 0.7])

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    quality_indicator = "🟢 Excellent" if avg_score > 0.8 else "🟡 Good" if avg_score > 0.6 else "🔴 Poor"
                    st.metric("Average Relevance", f"{avg_score:.3f}", quality_indicator)

                with col_b:
                    st.metric("High-Quality Sources", f"{high_quality_sources}/{len(sources)}", f"{(high_quality_sources/len(sources)*100):.0f}%")

                with col_c:
                    context_richness = "🎯 Rich" if len(sources) >= 3 else "📄 Moderate" if len(sources) >= 2 else "📋 Limited"
                    st.metric("Sources Retrieved", f"{len(sources)}", context_richness)

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

def render_export_section():
    """Render enhanced CSV download functionality for all metrics"""
    st.markdown('<div class="section-header">📤 Download Metrics Data</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="export-section">
        <h3>💾 Download RAG Pipeline Metrics</h3>
        <p>Download real-time metrics data from the RAG pipeline components for analysis and reporting.
        <em>Files are updated automatically every 30 seconds by the streaming service.</em></p>
    </div>
    """, unsafe_allow_html=True)

    # Get available files
    available_files = ModernDashboard.get_available_metrics_files()

    if not available_files:
        st.warning("⚠️ No metrics files found. Ensure the streaming service is running and generating data.")
        return

    # Organize files by category
    streaming_files = {k: v for k, v in available_files.items() if 'streaming_data' in k or 'chunking' in k or 'embedding' in k or 'vector_db' in k}
    query_files = {k: v for k, v in available_files.items() if k not in streaming_files}

    # Streaming Metrics Section
    if streaming_files:
        st.markdown("### 📊 Live Streaming Pipeline Metrics")

        cols = st.columns(2)

        for i, (file_key, file_path) in enumerate(streaming_files.items()):
            with cols[i % 2]:
                # Load the CSV data
                df = ModernDashboard.load_csv_file(file_path)

                if not df.empty:
                    # File info
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))

                    # Display file info
                    st.markdown(f"**📁 {file_key.replace('_', ' ').title()}**")
                    st.caption(f"📈 {len(df)} records • 💾 {file_size:.1f} KB • 🕐 Updated: {last_modified.strftime('%H:%M:%S')}")

                    # Preview first few rows
                    with st.expander(f"👁️ Preview {file_key}", expanded=False):
                        st.dataframe(df.head(3), use_container_width=True)

                    # Convert DataFrame to CSV for download
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()

                    # Download button
                    st.download_button(
                        label=f"📥 Download {file_key}.csv",
                        data=csv_data,
                        file_name=f"{file_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=f"download_{file_key}",
                        help=f"Download {len(df)} records as CSV file"
                    )
                else:
                    st.info(f"📄 {file_key}: No data available yet")

    # Query Metrics Section
    if query_files:
        st.markdown("### 🧠 LLM Query Metrics")

        for file_key, file_path in query_files.items():
            df = ModernDashboard.load_csv_file(file_path)

            if not df.empty:
                col1, col2 = st.columns([3, 1])

                with col1:
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))

                    st.markdown(f"**📁 {file_key.replace('_', ' ').title()}**")
                    st.caption(f"📈 {len(df)} records • 💾 {file_size:.1f} KB • 🕐 Updated: {last_modified.strftime('%H:%M:%S')}")

                with col2:
                    # Convert DataFrame to CSV for download
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()

                    st.download_button(
                        label=f"📥 Download",
                        data=csv_data,
                        file_name=f"{file_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=f"download_query_{file_key}",
                        help=f"Download {len(df)} records as CSV file"
                    )

    # Combined download option
    st.markdown("### 📦 Bulk Download")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Download All Available Metrics**")
        st.caption("Combines all metrics files into a single ZIP archive for comprehensive analysis")

    with col2:
        if st.button("📦 Download All", type="primary"):
            # Create a ZIP file with all CSV data
            import zipfile

            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_key, file_path in available_files.items():
                    df = ModernDashboard.load_csv_file(file_path)
                    if not df.empty:
                        csv_buffer = io.StringIO()
                        df.to_csv(csv_buffer, index=False)
                        csv_data = csv_buffer.getvalue()

                        zip_file.writestr(f"{file_key}.csv", csv_data)

            zip_data = zip_buffer.getvalue()

            st.download_button(
                label="📥 Download ZIP",
                data=zip_data,
                file_name=f"rag_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                key="download_all_zip",
                help="Download all metrics as ZIP file"
            )

def render_sidebar():
    """Render simplified sidebar with connection status and system info"""
    with st.sidebar:
        st.markdown("## 🎯 Query Analysis Tools")

        # User Credentials Section
        st.markdown('<div class="info-header">🔐 User Credentials</div>', unsafe_allow_html=True)

        with st.expander("🔑 Configure Your Credentials", expanded=False):
            st.markdown("**Enter your credentials to test with your own data:**")

            # ClickHouse credentials
            st.markdown("**ClickHouse Database:**")
            clickhouse_host = st.text_input("ClickHouse Host",
                                           value=st.session_state.get('clickhouse_host', ''),
                                           placeholder="your-instance.clickhouse.cloud",
                                           help="Your ClickHouse Cloud host")
            clickhouse_user = st.text_input("ClickHouse User",
                                           value=st.session_state.get('clickhouse_user', 'default'),
                                           placeholder="default")
            clickhouse_password = st.text_input("ClickHouse Password",
                                               value=st.session_state.get('clickhouse_password', ''),
                                               type="password",
                                               placeholder="Your ClickHouse password")
            clickhouse_database = st.text_input("ClickHouse Database",
                                               value=st.session_state.get('clickhouse_database', 'default'),
                                               placeholder="default")

            # HuggingFace credentials
            st.markdown("**HuggingFace API:**")
            huggingface_token = st.text_input("HuggingFace Token",
                                             value=st.session_state.get('huggingface_token', ''),
                                             type="password",
                                             placeholder="hf_xxxxxxxxxxxxxxxxxxxx",
                                             help="Your HuggingFace API token for LLM access")

            # Save credentials button
            if st.button("💾 Save Credentials", type="primary"):
                # Store in session state
                st.session_state.clickhouse_host = clickhouse_host
                st.session_state.clickhouse_user = clickhouse_user
                st.session_state.clickhouse_password = clickhouse_password
                st.session_state.clickhouse_database = clickhouse_database
                st.session_state.huggingface_token = huggingface_token

                # Create temporary .env content
                env_content = f"""# Temporary user credentials for this session
CLICKHOUSE_HOST={clickhouse_host}
CLICKHOUSE_USER={clickhouse_user}
CLICKHOUSE_PASSWORD={clickhouse_password}
CLICKHOUSE_DATABASE={clickhouse_database}
CLICKHOUSE_PORT=8443
CLICKHOUSE_SECURE=true
HUGGINGFACE_HUB_TOKEN={huggingface_token}

# Default LLM settings
DEFAULT_LLM_MODEL=meta-llama/Llama-3.2-1B-Instruct
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=1000
DEFAULT_TOP_K=5
SUPPORTED_MODELS=meta-llama/Llama-3.2-1B-Instruct,meta-llama/Llama-3.2-3B-Instruct
"""

                # Write to temporary .env file
                try:
                    import os
                    with open('/tmp/.env.user', 'w') as f:
                        f.write(env_content)
                    st.success("✅ Credentials saved for this session!")
                    st.info("🔄 Restart services to use your credentials")
                except Exception as e:
                    st.error(f"❌ Error saving credentials: {str(e)}")

        # Connection status with colored header
        st.markdown('<div class="status-header">🔗 Connection Status</div>', unsafe_allow_html=True)
        try:
            response = requests.get(f"http://{API_GATEWAY_HOST}:{API_GATEWAY_PORT}/api/health", timeout=5)
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

        # Display current credentials status
        st.markdown('<div class="info-header">🔐 Credentials Status</div>', unsafe_allow_html=True)
        if st.session_state.get('clickhouse_host'):
            st.success("✅ Credentials Configured")
            st.info(f"**ClickHouse:** {st.session_state.get('clickhouse_host', 'Not set')[:20]}...")
            st.info(f"**HuggingFace:** {'✅ Set' if st.session_state.get('huggingface_token') else '❌ Not set'}")
        else:
            st.warning("⚠️ Using Demo Mode")
            st.info("Configure your credentials above to use your own data")

        # System info with colored header
        st.markdown('<div class="info-header">ℹ️ System Information</div>', unsafe_allow_html=True)
        st.info(f"**Dashboard Version:** 2.1.0 Fixed")

# Analysis views and batch testing functionality removed as requested

def main():
    """Main dashboard application - focused on LLM query testing"""
    render_header()

    # Sidebar controls
    render_sidebar()

    # Initialize metrics data if needed
    if 'metrics_data' not in st.session_state:
        st.session_state.metrics_data = {}
        st.session_state.last_update = datetime.now()

    # Main dashboard content only (analysis views removed)
    render_llm_query_interface()
    render_query_history()

    st.markdown("<br>", unsafe_allow_html=True)

    render_export_section()

    # Technical architecture note
    st.markdown("""
    <div style="background: #e8f4fd; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #2196F3; margin-top: 2rem;">
        <h3>🏗️ Advanced Technical Architecture</h3>
        <p>✅ <strong>Real-time Pipeline:</strong> Async streaming with live financial data processing:</p>
        <ul>
            <li>📡 <strong>Async Data Streaming:</strong> Yahoo Finance → gRPC → ClickHouse (sub-second latency)</li>
            <li>🤖 <strong>Transformers Pipeline:</strong> HuggingFace sentence-transformers → PyTorch MPS GPU</li>
            <li>🧠 <strong>LLM Integration:</strong> Llama 3.2 with LangChain RAG → 10x Apple Silicon acceleration</li>
            <li>🗄️ <strong>Vector Database:</strong> ClickHouse Cloud with real-time indexing and reindexing detection</li>
            <li>⚡ <strong>Performance Monitoring:</strong> 30-second CSV exports with comprehensive metrics</li>
        </ul>
        <p>🎯 <strong>Production Features:</strong> gRPC microservices • Protocol Buffers • Docker multi-stage builds • Poetry dependency management</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
