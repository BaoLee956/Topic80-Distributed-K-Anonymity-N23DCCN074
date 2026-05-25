from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, Optional

import requests


ROOT_DIR = os.path.dirname(__file__)


class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def _supports_color() -> bool:
    if not sys.stdout.isatty():
        return False
    if os.environ.get("NO_COLOR"):
        return False
    return True


USE_COLOR = _supports_color()


def _c(text: str, color: str) -> str:
    if not USE_COLOR:
        return text
    return f"{color}{text}{Style.RESET}"


def _banner(title: str) -> None:
    line = "=" * 86
    print(_c(line, Style.DIM))
    print(_c(title, Style.BOLD + Style.CYAN))
    print(_c(line, Style.DIM))


def _pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def start_node(port: int, peers: str) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "app.py", "--port", str(port), "--peers", peers],
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def terminate_process(proc: Optional[subprocess.Popen]) -> None:
    if proc is None:
        return
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass


def wait_ready(port: int, timeout_s: float = 10.0) -> None:
    url = f"http://127.0.0.1:{port}/openapi.json"
    deadline = time.time() + timeout_s
    last_exc: Optional[Exception] = None

    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=1)
            if resp.status_code == 200:
                return
        except requests.exceptions.RequestException as exc:
            last_exc = exc
        time.sleep(0.4)

    raise RuntimeError(f"Node {port} chưa sẵn sàng sau {timeout_s}s. Last error: {last_exc}")


def call_anonymize(age: str, zip_code: str, timeout_s: float = 15.0) -> Dict[str, Any]:
    url = "http://127.0.0.1:8001/anonymize"
    resp = requests.get(url, params={"age": age, "zip_code": zip_code}, timeout=timeout_s)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    node_8001: Optional[subprocess.Popen] = None
    node_8002: Optional[subprocess.Popen] = None
    node_8003: Optional[subprocess.Popen] = None

    try:
        _banner("SETUP | Starting 3 distributed nodes (8001, 8002, 8003)")
        node_8001 = start_node(8001, "8002,8003")
        node_8002 = start_node(8002, "8001,8003")
        node_8003 = start_node(8003, "8001,8002")

        time.sleep(3)

        wait_ready(8001)
        wait_ready(8002)
        wait_ready(8003)
        print(_c("All nodes are up.", Style.GREEN))

        _banner("SCENARIO 1 | Ideal Case (age=22, zip_code=70001) => info_loss == 0")
        res1 = call_anonymize(age="22", zip_code="70001")
        print(_pretty(res1))
        assert res1.get("success") is True, "Scenario 1 failed: success != True"
        assert res1.get("info_loss") == 0, "Scenario 1 failed: info_loss != 0"
        print(_c("PASS: info_loss == 0", Style.GREEN))

        _banner("SCENARIO 2 | Generalization (age=34, zip_code=70129) => info_loss > 0, zip_code contains '*'")
        res2 = call_anonymize(age="34", zip_code="70129")
        print(_pretty(res2))
        assert res2.get("success") is True, "Scenario 2 failed: success != True"
        assert (res2.get("info_loss") or 0) > 0, "Scenario 2 failed: info_loss is not > 0"
        generalized_zip = ((res2.get("generalized_data") or {}).get("zip_code")) or ""
        assert "*" in generalized_zip, "Scenario 2 failed: generalized_data.zip_code does not contain '*'"
        print(_c(f"PASS: generalized zip_code = {generalized_zip}", Style.GREEN))

        _banner("SCENARIO 3 | Fault Tolerance (kill Node 8002) => success == True")
        terminate_process(node_8002)
        node_8002 = None
        print(_c("Đã đánh sập Node 8002. Đang đợi timeout...", Style.YELLOW))

        res3 = call_anonymize(age="45", zip_code="70300", timeout_s=20.0)
        print(_pretty(res3))
        assert res3.get("success") is True, "Scenario 3 failed: success != True"
        print(_c("PASS: system still succeeds with Node 8002 down", Style.GREEN))

        _banner("DONE | End-to-End scenarios completed")
    finally:
        terminate_process(node_8001)
        terminate_process(node_8002)
        terminate_process(node_8003)


if __name__ == "__main__":
    main()

