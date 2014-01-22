"""Global default settings."""

# Depth limit when recursively crawling.
MAX_DEPTH = 1

# The more the numerical value, the higher the log level,
# WARN by default.
LOG_LEVEL = 3

# The Item processor class object
ITEM_PROCESSOR = 'threaded_spider.core.itemproc.ItemProc'
