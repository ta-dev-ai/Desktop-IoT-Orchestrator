"""Runtime process registry for services started by the backend."""

from __future__ import annotations

import subprocess
from typing import Optional


broker_process: Optional[subprocess.Popen] = None
subscriber_process: Optional[subprocess.Popen] = None


def is_process_running(process: Optional[subprocess.Popen]) -> bool:
    return process is not None and process.poll() is None


def stop_process(process: Optional[subprocess.Popen], timeout: float = 3.0) -> bool:
    if not is_process_running(process):
        return False

    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=timeout)
    return True
