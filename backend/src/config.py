"""
Configuration settings for XBRL Search application.
"""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
TAXONOMIES_DIR = BASE_DIR / "taxonomies"

# Taxonomy paths
US_GAAP_ENTRY_POINT = TAXONOMIES_DIR / "us-gaap-2025" / "entire" / "us-gaap-entryPoint-all-2025.xsd"

# SEC EDGAR settings
SEC_BASE_URL = "https://data.sec.gov"
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions"
SEC_API_DELAY = 0.1  # Delay between SEC API requests (seconds)

# User agent for SEC requests (required by SEC)
SEC_USER_AGENT = "XBRL-Searcher 1.0 educational@example.com"

# Cache settings
CACHE_DIR = BASE_DIR / "cache"
CACHE_EXPIRY_HOURS = 24

# Arelle settings
ARELLE_LOG_LEVEL = "WARNING"  # Reduce Arelle logging noise

# API Settings
API_TITLE = "XBRL Search API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Search and analyze XBRL financial documents"

# Server Settings
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True

# Logging
LOG_LEVEL = "INFO"

# Simple settings object (instead of Pydantic BaseSettings)
class SimpleSettings:
    """Simple settings class without Pydantic dependency."""
    
    def __init__(self):
        # API Settings
        self.api_title = API_TITLE
        self.api_version = API_VERSION
        self.api_description = API_DESCRIPTION
        
        # Server Settings
        self.host = HOST
        self.port = PORT
        self.debug = DEBUG
        
        # Taxonomy Settings
        self.taxonomy_path = US_GAAP_ENTRY_POINT
        
        # SEC Settings
        self.sec_base_url = SEC_BASE_URL
        self.sec_archives_url = SEC_ARCHIVES_URL
        self.sec_company_facts_url = SEC_COMPANY_FACTS_URL
        self.sec_submissions_url = SEC_SUBMISSIONS_URL
        self.sec_user_agent = SEC_USER_AGENT
        self.sec_api_delay = SEC_API_DELAY
        
        # Cache Settings
        self.cache_dir = CACHE_DIR
        self.cache_expiry_hours = CACHE_EXPIRY_HOURS
        
        # Logging
        self.log_level = LOG_LEVEL
        self.arelle_log_level = ARELLE_LOG_LEVEL

# Create settings instance
settings = SimpleSettings()

# Ensure directories exist
CACHE_DIR.mkdir(exist_ok=True)