# Launcher for GAACA v2.0 Interactive Session
import sys
from pathlib import Path

cur_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(cur_dir))

from agent_v2.interactive_agent import start_interactive_session

if __name__ == "__main__":
    start_interactive_session()
