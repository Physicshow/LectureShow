import logging

# Logging setup
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Debug flag (set to True if needed)
DEBUG_MODE = False

# Mouse event filtering flag
FILTER_SUSPICIOUS_CLICKS = True 