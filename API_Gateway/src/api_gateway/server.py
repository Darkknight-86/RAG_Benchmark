"""
API Gateway Server - Main server module for the API Gateway.

This module sets up and runs the API Gateway server, including the metrics
collection and dashboard functionality.
"""

import logging
import atexit
from flask import Flask

from .metrics import MetricsCollector, RAGBenchmarks, MetricsDashboard

class APIGatewayServer:
    """Main API Gateway server class."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app = Flask(__name__)

        # Initialize metrics components
        self.benchmarks = RAGBenchmarks()
        self.collector = MetricsCollector(self.benchmarks)
        self.dashboard = MetricsDashboard(self.benchmarks, self.collector)

        # Register the dashboard blueprint
        self.app.register_blueprint(self.dashboard.blueprint, url_prefix='/api')

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Register shutdown handler
        atexit.register(self._shutdown)

    def _shutdown(self):
        """Clean up resources when the server shuts down."""
        self.logger.info("Shutting down API Gateway server...")
        # Stop all active metric collections
        for service in list(self.collector.active_services):
            self.collector.stop_collection_for_service(service)

    def run(self, host: str = '0.0.0.0', port: int = 8000, debug: bool = False):
        """Run the API Gateway server."""
        self.logger.info(f"Starting API Gateway server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def create_app():
    """Create and configure the Flask application."""
    server = APIGatewayServer()
    return server.app

if __name__ == '__main__':
    server = APIGatewayServer()
    server.run()