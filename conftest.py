"""Rod-conftest. Tilstedeværelsen alene får pytest til at lægge projektroden på
sys.path, så `validator` og `app` kan importeres uanset hvordan testene startes
(`pytest`, `python -m pytest`, fra IDE). Suppleres af pyproject.toml [pythonpath].
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
