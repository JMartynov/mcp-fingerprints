import sys
from pathlib import Path

# Add project root to PYTHONPATH so tests can import from 'scripts'
sys.path.insert(0, str(Path(__file__).parent.parent))
