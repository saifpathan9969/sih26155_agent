# Root test runner for GAACA v2.0 verification suite
import sys
import subprocess
from pathlib import Path

inner_root = Path(__file__).resolve().parent / "sih26155_agent"
sys.path.insert(0, str(inner_root))

test_modules = [
    "agent_v2.tests.test_phase0",
    "agent_v2.tests.test_phase1",
    "agent_v2.tests.test_phase2",
    "agent_v2.tests.test_phase3_capabilities",
    "agent_v2.tests.test_phase4_security",
    "agent_v2.tests.test_phase5_memory",
    "agent_v2.tests.test_safety",
    "agent_v2.tests.test_mission_indep",
]

if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING ALL GAACA v2.0 VERIFICATION SUITES")
    print("=" * 70)
    failed = []
    for mod in test_modules:
        res = subprocess.run([sys.executable, "-m", mod], cwd=str(inner_root))
        if res.returncode != 0:
            failed.append(mod)
    print("\n" + "=" * 70)
    if not failed:
        print("ALL 8 VERIFICATION SUITES PASSED (100% SUCCESS)")
    else:
        print(f"FAILED SUITES: {failed}")
    print("=" * 70)
