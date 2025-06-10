"""
Global warning suppression for production deployment.
Import this module at the top of any main service file to silence common warnings.
"""

import warnings
import os

# Suppress common development warnings for production
warnings.filterwarnings("ignore", category=UserWarning, module="clickhouse_connect")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Suppress multiprocessing warnings
warnings.filterwarnings("ignore", message="resource_tracker")

# Environment variable to suppress additional warnings
os.environ.setdefault('PYTHONWARNINGS', 'ignore')

# Streamlit specific warnings
os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
os.environ.setdefault('STREAMLIT_LOGGER_LEVEL', 'ERROR')

print("✅ Production warning suppression activated")