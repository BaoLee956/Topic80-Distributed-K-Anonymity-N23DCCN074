"""
Script test độc lập cho đồ án "Distributed K-Anonymity for JSON: Health Surveys".

Yêu cầu đề bài:
- Dùng requests gọi đến http://127.0.0.1:8001/anonymize
- Test case 1: age="22", zip_code="70001"
- Test case 2: age="34", zip_code="70129"
- In kết quả đẹp và dễ đọc:
    + Thời gian phản hồi
    + Trạng thái success
    + total_count, info_loss, iterations
    + Dữ liệu đã làm mờ (generalized_data)
    + Chi tiết đếm từng node (per_node_counts)
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict

import requests


API_URL = "http://127.0.0.1:8001/anonymize"


def _line(char: str = "=", width: int = 80) -> str:
    """
    Tạo 1 dòng phân cách giúp output dễ nhìn.
    """

    return char * width


def _pretty_json(obj: Any) -> str:
    """
    In JSON đẹp (indent) để nộp đồ án dễ đọc.
    """

    return json.dumps(obj, ensure_ascii=False, indent=2)


def _print_kv(key: str, value: Any, key_width: int = 18) -> None:
    """
    In key-value theo cột, giúp nhìn nhanh các chỉ số quan trọng.
    """

    key_fmt = f"{key}:".ljust(key_width)
    print(f"{key_fmt}{value}")


def run_test_case(age: str, zip_code: str) -> None:
    """
    Chạy 1 test case gọi /anonymize và in kết quả.

    Lưu ý:
    - timeout được set để tránh treo nếu server không phản hồi
    """

    print(_line("="))
    print(f"TEST CASE | age={age!r}, zip_code={zip_code!r}")
    print(_line("-"))

    start = time.perf_counter()
    try:
        resp = requests.get(
            API_URL,
            params={"age": age, "zip_code": zip_code},
            timeout=5,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
    except requests.exceptions.RequestException as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        _print_kv("Response time", f"{elapsed_ms:.2f} ms")
        _print_kv("Status", "FAILED")
        _print_kv("Error", str(exc))
        return

    _print_kv("Response time", f"{elapsed_ms:.2f} ms")
    _print_kv("HTTP status", resp.status_code)

    try:
        data: Dict[str, Any] = resp.json()
    except ValueError:
        _print_kv("Parse JSON", "FAILED")
        print("Raw response:")
        print(resp.text)
        return

    print(_line("-"))
    _print_kv("Success", data.get("success"))
    _print_kv("Total count", data.get("total_count"))
    _print_kv("Info loss", data.get("info_loss"))
    _print_kv("Iterations", data.get("iterations"))

    generalized = data.get("generalized_data", {})
    per_node = data.get("per_node_counts", {})

    print(_line("-"))
    print("Generalized data:")
    print(_pretty_json(generalized))

    print(_line("-"))
    print("Per-node counts:")
    if isinstance(per_node, dict) and per_node:
        for node, count in per_node.items():
            print(f"- {str(node).ljust(30)} {count}")
    else:
        print("- (không có dữ liệu per_node_counts)")

    print(_line("-"))
    print("Full response JSON:")
    print(_pretty_json(data))


def main() -> None:
    """
    Chạy 2 test case theo đúng yêu cầu đề bài.
    """

    run_test_case(age="22", zip_code="70001")
    run_test_case(age="34", zip_code="70129")
    print(_line("="))


if __name__ == "__main__":
    main()

