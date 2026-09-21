# Root launcher for GAACA v2.0 Demo
import sys
from pathlib import Path

inner_root = Path(__file__).resolve().parent / "sih26155_agent"
sys.path.insert(0, str(inner_root))

from agent_v2.demo import run_demo

if __name__ == "__main__":
    run_demo()
