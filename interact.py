# Launcher for GAACA v2.0 Interactive Session
import sys
from pathlib import Path

outer_dir = Path(__file__).resolve().parent
inner_dir = outer_dir / "sih26155_agent"

if inner_dir.exists():
    sys.path.insert(0, str(inner_dir))
else:
    sys.path.insert(0, str(outer_dir))

from agent_v2.interactive_agent import start_interactive_session

if __name__ == "__main__":
    start_interactive_session()
