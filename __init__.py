# Frontend extension (JS)
WEB_DIRECTORY = "./js"

# Python nodes
from .nodes.TextCleanerSplitter import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Required exports
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]