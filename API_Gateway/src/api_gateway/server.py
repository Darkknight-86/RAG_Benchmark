"""
API Gateway Server - Main server module for the API Gateway.
"""

import logging
import os
from flask import Flask
from dotenv import load_dotenv
from api_gateway.routes import register_routes

load_dotenv()

class APIGatewayServer:
    """Main API Gateway server class."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app = Flask(__name__)

        # Configure the app
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

        # Register routes
        register_routes(self.app)

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def run(self, host: str = '0.0.0.0', port: int = 8000, debug: bool = False):
        """Run the API Gateway server."""
        self.logger.info(f"Starting API Gateway server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def create_app():
    """Create and configure the Flask application."""
    server = APIGatewayServer()
    return server.app

def main():
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()