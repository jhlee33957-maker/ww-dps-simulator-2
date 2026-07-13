from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import run_command

    with tempfile.TemporaryDirectory(prefix="guarded-timeout-") as temp_dir:
        log_dir = Path(temp_dir) / "logs"
        try:
            run_command(
                [sys.executable, "-c", "import time; print('start'); time.sleep(10)"],
                log_dir=log_dir,
                stage_label="timeout",
                timeout_seconds=0.2,
            )
        except RuntimeError as exc:
            message = str(exc)
            assert "timeout" in message
            assert "stdout_log" in message
            assert (log_dir / "timeout.stdout.log").exists()
            assert (log_dir / "timeout.stderr.log").exists()
        else:
            raise AssertionError("timeout command unexpectedly completed")
    print("guarded_ppo_stage_timeout_smoke_test ok")


if __name__ == "__main__":
    main()
