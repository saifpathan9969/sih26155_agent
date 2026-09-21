# Launcher for GAACA v2.0 — 3D Web Interface
import sys
from pathlib import Path

outer_dir = Path(__file__).resolve().parent
inner_dir = outer_dir / "sih26155_agent"

if inner_dir.exists():
    sys.path.insert(0, str(inner_dir))
else:
    sys.path.insert(0, str(outer_dir))

from web_ui.server import app

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  VigilNet v2.0 — 3D Web Interface")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
