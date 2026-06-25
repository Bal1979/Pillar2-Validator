"""Rod-conftest. Tilstedeværelsen alene får pytest til at lægge projektroden på
sys.path, så `validator` og `app` kan importeres uanset hvordan testene startes
(`pytest`, `python -m pytest`, fra IDE). Suppleres af pyproject.toml [pythonpath].

Sætter også et isoleret test-miljø for den centrale brugerstyring (balai_auth):
en frisk temp-SQLite som auth-DB og ingen delt Postgres, så testene aldrig rører
produktionsdatabasen. Sættes FØR app importeres, da init_app/init_db kører ved
import.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

# --- Isoleret auth-DB til tests (må ske før 'import app') -------------------
os.environ.pop("DATABASE_URL", None)          # brug ikke delt Postgres i test
os.environ.setdefault("SECRET_KEY", "test-secret-key")
_AUTH_TEST_DB = os.path.join(tempfile.gettempdir(), "pillar2_test_auth.db")
try:
    os.remove(_AUTH_TEST_DB)                   # frisk DB ved hver testkørsel
except OSError:
    pass
os.environ["AUTH_DB_PATH"] = _AUTH_TEST_DB
