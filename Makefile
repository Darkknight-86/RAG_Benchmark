.PHONY: help setup lock install start stop clean test status dashboard start-streaming start-embeddings-grpc test-embeddings

# Default target
help:
	@echo "Financial RAG System - Available Commands:"
	@echo ""
	@echo "🚀 System Commands:"
	@echo "  make setup    - Complete setup for fresh clone (lock + install)"
	@echo "  make start    - Start all services"
	@echo "  make stop     - Stop all services"
	@echo "  make status   - Check service status"
	@echo "  make clean    - Clean up processes and temporary files"
	@echo ""
	@echo "🔧 Development Commands:"
	@echo "  make lock     - Generate lock files for all services"
	@echo "  make install  - Install dependencies for all services"
	@echo "  make test     - Run tests for all services"
	@echo ""
	@echo "📊 Individual Services:"
	@echo "  make dashboard           - Start Enhanced Dashboard (redesigned)"
	@echo "  make start-streaming     - Start Embeddings live data streaming"
	@echo "  make start-embeddings-grpc - Start Embeddings gRPC service"
	@echo "  make test-embeddings     - Test Embeddings microservice standalone"
	@echo ""
	@echo "🎯 Redesigned System Features:"
	@echo "  • FastAPI Gateway (no Flask conflicts)"
	@echo "  • Enhanced Dashboard with LLM query testing"
	@echo "  • Real-time VD load time tracking"
	@echo "  • Dual metrics system (streaming + RAG)"
	@echo "  • CSV export functionality"
	@echo ""

# Complete setup for fresh clone
setup: lock install
	@echo "🎉 Project setup complete! Ready to start services with 'make start'"

# Generate lock files for all services
lock:
	@echo "🔒 Generating lock files for all services..."
	@echo "  → Locking Embeddings dependencies..."
	cd Embeddings && poetry lock
	@echo "  → Locking LLM service dependencies..."
	cd LLM && poetry lock
	@echo "  → Locking API Gateway dependencies..."
	cd API_Gateway && poetry lock
	@echo "  → Locking Ingestion service dependencies..."
	cd Ingestion && poetry lock
	@echo "  → Locking UI service dependencies..."
	cd UI && poetry lock
	@echo "✅ All lock files generated!"

# Install dependencies for all services
install:
	@echo "📦 Installing dependencies for all services..."
	@echo "  → Installing Embeddings dependencies..."
	cd Embeddings && poetry install --only main
	@echo "  → Installing LLM service dependencies..."
	cd LLM && poetry install --only main
	@echo "  → Installing API Gateway dependencies..."
	cd API_Gateway && poetry install --only main
	@echo "  → Installing Ingestion service dependencies..."
	cd Ingestion && poetry install --only main
	@echo "  → Installing UI service dependencies..."
	cd UI && poetry install --only main
	@echo "✅ All dependencies installed!"

# Start all services (REDESIGNED SYSTEM)
start:
	@echo "🚀 Starting Financial RAG system (Redesigned)..."
	@echo "  → Connecting to hosted ClickHouse service..."
	@echo "  → Starting Embeddings service..."
	cd Embeddings && PYTHONPATH=src poetry run python src/main.py &
	@sleep 3
	@echo "  → Starting LLM service..."
	cd LLM && PYTHONPATH=src poetry run python src/main.py &
	@sleep 3
	@echo "  → Starting FastAPI Gateway (NEW)..."
	cd API_Gateway && PYTHONPATH=src poetry run uvicorn api_gateway.fastapi_server:app --host 0.0.0.0 --port 8000 &
	@sleep 3
	@echo "  → Starting Enhanced Dashboard (NEW)..."
	cd API_Gateway && PYTHONPATH=src poetry run streamlit run src/dashboard/enhanced_streamlit_dashboard.py --server.port 8502 &
	@sleep 3
	@echo "  → Starting Live Streaming Service..."
	cd Embeddings && PYTHONPATH=src poetry run python src/streaming.py &
	@echo ""
	@echo "✅ All services started!"
	@echo ""
	@echo "📊 Service URLs (REDESIGNED):"
	@echo "  • FastAPI Gateway:   http://localhost:8000"
	@echo "  • Enhanced Dashboard: http://localhost:8502"
	@echo "  • Embeddings:        localhost:50051 (gRPC)"
	@echo "  • LLM Service:       localhost:50054 (gRPC)"
	@echo "  • Live Streaming:    Active (yliveticker → ClickHouse)"
	@echo "  • ClickHouse:        [Hosted Service - Websocket]"
	@echo ""
	@echo "🎯 NEW FEATURES:"
	@echo "  • LLM Query Testing with beautiful UI"
	@echo "  • Real-time VD load time tracking"
	@echo "  • Dual metrics system (streaming + RAG)"
	@echo "  • CSV export functionality"
	@echo "  • No more Flask/gRPC conflicts!"

# Stop all services
stop:
	@echo "🛑 Stopping all services..."
	@pkill -f "src/main.py" || true
	@pkill -f "uvicorn" || true
	@pkill -f "api_gateway.fastapi_server" || true
	@pkill -f "streamlit" || true
	@pkill -f "enhanced_metrics" || true
	@pkill -f "streaming.py" || true
	@echo "✅ All services stopped!"

# Check service status
status:
	@echo "📊 Service Status (REDESIGNED SYSTEM):"
	@echo ""
	@echo "FastAPI Gateway (port 8000):"
	@curl -s http://localhost:8000/api/health 2>/dev/null && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo ""
	@echo "Enhanced Dashboard (port 8502):"
	@curl -s http://localhost:8502 2>/dev/null >/dev/null && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo ""
	@echo "Embeddings Service (gRPC port 50051):"
	@lsof -i :50051 >/dev/null 2>&1 && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo ""
	@echo "LLM Service (gRPC port 50054):"
	@lsof -i :50054 >/dev/null 2>&1 && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo ""
	@echo "Live Streaming Service:"
	@pgrep -f "streaming.py" >/dev/null 2>&1 && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo ""
	@echo "ClickHouse: [Hosted Service - Check your websocket connection]"

# Run tests across all services
test:
	@echo "🧪 Running tests for all services..."
	@echo "  → Testing Embeddings..."
	cd Embeddings && PYTHONPATH=src poetry run pytest || true
	@echo "  → Testing LLM service..."
	cd LLM && PYTHONPATH=src poetry run pytest || true
	@echo "  → Testing API Gateway..."
	cd API_Gateway && PYTHONPATH=src poetry run pytest || true
	@echo "  → Testing Ingestion..."
	cd Ingestion && PYTHONPATH=src poetry run pytest || true
	@echo "  → Testing UI..."
	cd UI && PYTHONPATH=src poetry run pytest || true
	@echo "✅ Tests completed!"

# Clean up processes and temporary files
clean: stop
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"
	@echo ""
	@echo "Note: ClickHouse is a hosted service - no local cleanup needed"

# Start standalone dashboard (REDESIGNED)
dashboard:
	@echo "🚀 Starting Enhanced Dashboard (standalone)..."
	cd API_Gateway && PYTHONPATH=src poetry run streamlit run src/dashboard/enhanced_streamlit_dashboard.py --server.port 8502

# Start Embeddings streaming service only (live financial data)
start-streaming:
	@echo "🔄 Starting Embeddings streaming service..."
	@echo "  → Processing live financial data (yliveticker → database)"
	cd Embeddings && PYTHONPATH=src poetry run python src/streaming.py

# Start Embeddings gRPC service only (for API Gateway)
start-embeddings-grpc:
	@echo "📊 Starting Embeddings gRPC service..."
	@echo "  → Ready to serve Query/Benchmark requests on port 50051"
	cd Embeddings && PYTHONPATH=src poetry run python src/main.py

# Test Embeddings microservice standalone
test-embeddings:
	@echo "🧪 Testing Embeddings microservice standalone..."
	@echo "  → Testing streaming service initialization..."
	cd Embeddings && PYTHONPATH=src poetry run python -c "import sys; sys.path.append('src'); from streaming import streamer; print('✅ Streaming service OK'); print(f'📊 Adapters: {streamer.database.get_available_adapters()}')"
	@echo "  → Testing gRPC service initialization..."
	cd Embeddings && PYTHONPATH=src poetry run python -c "import sys; sys.path.append('src'); from main import EmbeddingsRAGService; service = EmbeddingsRAGService(); print('✅ gRPC service OK'); print(f'📊 Database: {service.db.primary_adapter_type}')"
	@echo "✅ Embeddings microservice tests completed!"