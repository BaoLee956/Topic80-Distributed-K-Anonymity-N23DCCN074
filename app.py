from __future__ import annotations

import argparse
import random
from typing import Dict, List, Tuple

import requests
import uvicorn
from fastapi import FastAPI, Query
from pydantic import BaseModel

K_ANONYMITY = 3
MAX_ITERATIONS = 50


class HealthRecord(BaseModel):
    Age: str
    ZipCode: str
    Disease: str


def _build_mock_data(port: int) -> List[HealthRecord]:
    base_records = [
        HealthRecord(Age="22", ZipCode="70001", Disease="Flu"),
        HealthRecord(Age="22", ZipCode="70001", Disease="Cold"),
        HealthRecord(Age="22", ZipCode="70001", Disease="Allergy"),
        HealthRecord(Age="34", ZipCode="70129", Disease="Diabetes"),
        HealthRecord(Age="34", ZipCode="70129", Disease="Hypertension"),
        HealthRecord(Age="34", ZipCode="70129", Disease="Asthma"),
        HealthRecord(Age="19", ZipCode="70012", Disease="Flu"),
        HealthRecord(Age="25", ZipCode="70015", Disease="Migraine"),
        HealthRecord(Age="29", ZipCode="70110", Disease="Anxiety"),
        HealthRecord(Age="41", ZipCode="70122", Disease="Arthritis"),
        HealthRecord(Age="52", ZipCode="70090", Disease="Heart Disease"),
        HealthRecord(Age="37", ZipCode="70210", Disease="Back Pain"),
    ]

    rng = random.Random(port)
    records = list(base_records)
    rng.shuffle(records)

    extra_pool = [
        HealthRecord(Age="22", ZipCode="70001", Disease="Covid-19"),
        HealthRecord(Age="34", ZipCode="70129", Disease="Flu"),
        HealthRecord(Age="33", ZipCode="70120", Disease="Depression"),
        HealthRecord(Age="35", ZipCode="70128", Disease="Obesity"),
        HealthRecord(Age="45", ZipCode="70040", Disease="Kidney Disease"),
        HealthRecord(Age="28", ZipCode="70002", Disease="Dermatitis"),
        HealthRecord(Age="31", ZipCode="70100", Disease="Gastritis"),
    ]

    extra_count = 2 + (port % 4)
    extras = rng.sample(extra_pool, k=min(extra_count, len(extra_pool)))
    records.extend(extras)

    for idx, rec in enumerate(records):
        if idx % 7 == (port % 7):
            records[idx] = HealthRecord(
                Age=rec.Age,
                ZipCode=rec.ZipCode,
                Disease=f"{rec.Disease}-P{port}",
            )

    return records[:15]


def _normalize_peers(peers_raw: str, self_port: int) -> List[str]:
    if not peers_raw:
        return []

    peers: List[str] = []
    for token in peers_raw.split(","):
        token = token.strip()
        if not token:
            continue

        if token.isdigit():
            url = f"http://127.0.0.1:{int(token)}"
        else:
            if token.startswith("http://") or token.startswith("https://"):
                url = token
            else:
                url = f"http://{token}"

        url = url.rstrip("/")

        if url.endswith(f":{self_port}"):
            continue

        peers.append(url)

    unique = sorted(set(peers))
    return unique


def _parse_age_query(age_query: str) -> Tuple[int | None, int | None]:
    try:
        if "±" in age_query:
            center_str, delta_str = age_query.split("±", 1)
            center = int(center_str.strip())
            delta = int(delta_str.strip()) if delta_str.strip() else 0
            return center, delta

        return int(age_query.strip()), 0
    except ValueError:
        return None, None


def _match_age(record_age: str, age_query: str) -> bool:
    if "±" not in age_query:
        return record_age == age_query

    center, delta = _parse_age_query(age_query)
    if center is None or delta is None:
        return record_age == age_query

    try:
        record_value = int(record_age)
    except ValueError:
        return False

    return (center - delta) <= record_value <= (center + delta)


def _match_zip(record_zip: str, zip_query: str) -> bool:
    if "*" not in zip_query:
        return record_zip == zip_query

    prefix = zip_query.split("*", 1)[0]
    if prefix == "":
        return True
    return record_zip.startswith(prefix)


def _count_matching_records(
    records: List[HealthRecord],
    age_query: str,
    zip_query: str,
) -> int:
    count = 0
    for rec in records:
        if _match_age(rec.Age, age_query) and _match_zip(rec.ZipCode, zip_query):
            count += 1
    return count


def generalize(age: str, zip_code: str) -> Tuple[str, str, int]:
    info_loss_inc = 1

    if zip_code and any(ch != "*" for ch in zip_code):
        chars = list(zip_code)
        for i in range(len(chars) - 1, -1, -1):
            if chars[i] != "*":
                chars[i] = "*"
                return age, "".join(chars), info_loss_inc

    center, delta = _parse_age_query(age)
    if center is None or delta is None:
        return age, zip_code, info_loss_inc

    if "±" in age:
        new_age = f"{center}±{delta + 5}"
    else:
        new_age = f"{center}±5"

    return new_age, zip_code, info_loss_inc


def create_app(port: int, peers: List[str]) -> FastAPI:
    app = FastAPI(title="Distributed K-Anonymity Node")
    app.state.port = port
    app.state.peers = peers
    app.state.records = _build_mock_data(port)

    @app.get("/count_quasi")
    def count_quasi(
        age: str = Query(..., description="Age: '22' hoặc '34±5'"),
        zip_code: str = Query(..., description="ZipCode: '70001' hoặc '70***'"),
    ) -> Dict[str, int]:
        records: List[HealthRecord] = app.state.records
        return {"count": _count_matching_records(records, age, zip_code)}

    @app.get("/anonymize")
    def anonymize(
        age: str = Query(..., description="Age: '22' hoặc '34±5'"),
        zip_code: str = Query(..., description="ZipCode: '70001' hoặc '70***'"),
    ) -> Dict:
        current_age = age
        current_zip = zip_code

        info_loss = 0
        per_node_counts: Dict[str, int] = {}

        records: List[HealthRecord] = app.state.records
        peers_list: List[str] = app.state.peers
        self_port: int = app.state.port

        for iteration in range(1, MAX_ITERATIONS + 1):
            per_node_counts = {}

            local_count = _count_matching_records(records, current_age, current_zip)
            per_node_counts[f"local:{self_port}"] = local_count

            for peer in peers_list:
                url = f"{peer}/count_quasi"
                try:
                    resp = requests.get(
                        url,
                        params={"age": current_age, "zip_code": current_zip},
                        timeout=2,
                    )
                    resp.raise_for_status()
                    peer_count = int(resp.json().get("count", 0))
                except requests.exceptions.RequestException:
                    print(
                        f"[CẢNH BÁO] Peer {peer} không phản hồi hoặc lỗi. "
                        "Gán count=0 và tiếp tục..."
                    )
                    peer_count = 0
                except (ValueError, TypeError):
                    print(
                        f"[CẢNH BÁO] Peer {peer} trả về dữ liệu không hợp lệ. "
                        "Gán count=0 và tiếp tục..."
                    )
                    peer_count = 0

                per_node_counts[peer] = peer_count

            total_count = sum(per_node_counts.values())
            if total_count >= K_ANONYMITY:
                return {
                    "success": True,
                    "total_count": total_count,
                    "info_loss": info_loss,
                    "iterations": iteration,
                    "original_data": {"age": age, "zip_code": zip_code},
                    "generalized_data": {
                        "age": current_age,
                        "zip_code": current_zip,
                    },
                    "per_node_counts": per_node_counts,
                }

            current_age, current_zip, inc = generalize(current_age, current_zip)
            info_loss += inc

        return {
            "success": False,
            "total_count": sum(per_node_counts.values()) if per_node_counts else 0,
            "info_loss": info_loss,
            "iterations": MAX_ITERATIONS,
            "original_data": {"age": age, "zip_code": zip_code},
            "generalized_data": {"age": current_age, "zip_code": current_zip},
            "per_node_counts": per_node_counts,
        }

    return app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Distributed K-Anonymity Node (FastAPI)",
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Cổng chạy node (vd: 8001)",
    )
    parser.add_argument(
        "--peers",
        type=str,
        default="",
        help="Danh sách peers, phân tách bởi dấu phẩy. "
        "Ví dụ: '8002,8003' hoặc 'http://127.0.0.1:8002,http://127.0.0.1:8003'",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    peers = _normalize_peers(args.peers, args.port)
    app = create_app(args.port, peers)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        log_level="info",
    )

