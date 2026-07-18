from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manual_120s_bc_final_archive_integrity_smoke_test import candidate_121_fresh_extraction_check_commands


REPRESENTATIVE_SCRIPTS = (
    "scripts/aemeath_fusion_base_trigger_application_v121_smoke_test.py",
    "scripts/aemeath_fusion_natural_state_settlement_v121_smoke_test.py",
    "scripts/aemeath_fusion_qte_application_v121_smoke_test.py",
)


def main() -> None:
    provider = ROOT / "scripts/manual_120s_bc_final_archive_integrity_smoke_test.py"
    provider_text = provider.read_text(encoding="utf-8")
    assert "env.pop(\"PYTHONPATH\", None)" in provider_text
    commands = candidate_121_fresh_extraction_check_commands()
    paths = {command[1].replace("\\", "/") for command in commands}
    assert "scripts/candidate_121_standalone_test_import_portability_smoke_test.py" not in paths
    assert set(REPRESENTATIVE_SCRIPTS).issubset(paths)
    for path in REPRESENTATIVE_SCRIPTS:
        text = (ROOT / path).read_text(encoding="utf-8")
        if "from simulator." in text or "from characters." in text:
            assert "sys.path.insert(0, str(ROOT))" in text or "sys.path.insert(0, str(PROJECT_ROOT))" in text, path

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    for script in REPRESENTATIVE_SCRIPTS:
        completed = subprocess.run(
            [sys.executable, script], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30, check=False
        )
        assert completed.returncode == 0, f"{script}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    print("candidate_121_bounded_import_portability_smoke_test ok representatives=3")


if __name__ == "__main__":
    main()
