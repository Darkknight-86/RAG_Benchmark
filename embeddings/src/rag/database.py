import clickhouse_connect
from typing import Optional, Any, List
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory (two levels up from this file)
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / '.env')

def get_env_or_raise(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

@dataclass
class DatabaseConfig:
    host: str
    user: str
    password: str
    secure: bool = True
    port: int = 8443

class ClickHouseDatabase:
    _instance: Optional['ClickHouseDatabase'] = None
    _client: Optional[Any] = None

    def __new__(cls, config: Optional[DatabaseConfig] = None):
        if cls._instance is None:
            cls._instance = super(ClickHouseDatabase, cls).__new__(cls)
            cls._instance._initialize(config)
        return cls._instance

    def _initialize(self, config: Optional[DatabaseConfig] = None):
        if config is None:
            try:
                config = DatabaseConfig(
                    host=get_env_or_raise('CLICKHOUSE_HOST'),
                    user=get_env_or_raise('CLICKHOUSE_USER'),
                    password=get_env_or_raise('CLICKHOUSE_PASSWORD'),
                    secure=os.getenv('CLICKHOUSE_SECURE', 'true').lower() == 'true',
                    port=int(os.getenv('CLICKHOUSE_PORT', '8443'))
                )
            except ValueError as e:
                raise RuntimeError(f"Failed to initialize database configuration: {str(e)}")

        self._client = clickhouse_connect.get_client(
            host=config.host,
            user=config.user,
            password=config.password,
            secure=config.secure,
            port=config.port
        )

    @property
    def client(self):
        if self._client is None:
            raise RuntimeError("Database client not initialized")
        return self._client

    def execute_query(self, query: str, params: Optional[dict] = None) -> List[Any]:
        """
        Execute a query and return the results
        """
        return self.client.query(query, parameters=params).result_set

    def test_connection(self) -> bool:
        """
        Test the database connection
        """
        try:
            result = self.execute_query("SELECT 1")
            return result[0][0] == 1
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False

# Example usage:
if __name__ == '__main__':
    print("Environment variables:")
    for key, value in os.environ.items():
        if key.startswith('CLICKHOUSE_'):
            print(f"{key}={value}")

    try:
        # Initialize with default config from environment variables
        db = ClickHouseDatabase()

        # Test the connection
        if db.test_connection():
            print("Successfully connected to ClickHouse!")
        else:
            print("Failed to connect to ClickHouse")
    except Exception as e:
        print(f"Error: {str(e)}")