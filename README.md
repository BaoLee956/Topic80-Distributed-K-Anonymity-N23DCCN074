# Topic 80 - Distributed K-Anonymity for JSON: **Health Surveys** (Category 8)

## Abstract (Why)
This project implements a **peer-to-peer (P2P) distributed system** for **K-Anonymity** on JSON-based health survey records with **k = 3**.

Instead of collecting raw data into a centralized server (which increases privacy risk and network cost), each node keeps a **sharded subset** of the dataset and cooperates by exchanging only **aggregate counts**. The system automatically **generalizes** quasi-identifiers (**Age** and **ZipCode**) to reach **k = 3**, while tracking the privacy/utility trade-off using an **info_loss** score.

The network is designed to be **fault-tolerant**: if a node fails, other nodes continue anonymization by treating the failed peer’s contribution as **0** and generalizing further when needed.

---

## Project Structure
- **app.py**: FastAPI node implementation (API + anonymization algorithm + peer-to-peer querying).
- **data.json**: Raw test dataset (array of JSON objects with `Age`, `ZipCode`, `Disease`).
- **test_runner.py**: Calls Node **8001** and prints readable results for two test cases.
- **auto_test.py**: End-to-end orchestration script to start 3 nodes, run tests, simulate node failure, and teardown.

---

## Prerequisites
- **Python 3.x**
- Libraries: **FastAPI**, **Uvicorn**, **Requests**, **Pydantic**

---

## Installation

### 1) Create and activate a virtual environment
```bash
python -m venv .venv
```

Activate:

- Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

- macOS/Linux:
```bash
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install fastapi uvicorn requests pydantic
```

---

## How to Run the Distributed Network (3 Terminals)
Open **3 terminals** at the project root and run:

### Node 1 (port **8001**)
```bash
python app.py --port 8001 --peers 8002,8003
```

### Node 2 (port **8002**)
```bash
python app.py --port 8002 --peers 8001,8003
```

### Node 3 (port **8003**)
```bash
python app.py --port 8003 --peers 8001,8002
```

Each node exposes:
- Swagger UI: `http://127.0.0.1:<port>/docs`
- OpenAPI JSON: `http://127.0.0.1:<port>/openapi.json`

---

## Sharding (Data Fragmentation)
The dataset in **data.json** is sharded deterministically by port:
- `node_id = port % 3`
- Each record at index `idx` belongs to the node when `idx % 3 == node_id`

This creates **non-overlapping shards** across Node **8001**, **8002**, and **8003** (no duplicated records between nodes).

---

## API Overview
Main endpoint for anonymization:
- `GET /anonymize`
  - Query params:
    - `age` (string), e.g. `22` or generalized form like `34±5`
    - `zip_code` (string), e.g. `70001` or generalized form like `7012*`
  - Response fields (high level):
    - `success` (bool)
    - `total_count` (int): aggregated count across local + peers
    - `info_loss` (int): information loss due to generalization steps
    - `iterations` (int): number of generalization attempts
    - `generalized_data`: final generalized `(age, zip_code)`
    - `per_node_counts`: per-node contributions (failed peers are treated as **0**)

---

## Testing & Demo Scenarios (Most Important)
Use Swagger UI on Node 8001:

- Open: **http://127.0.0.1:8001/docs**
- Find endpoint: `GET /anonymize`
- Enter parameters and execute.

### Scenario 1 — The Ideal Case (No info loss)
Goal: the query already matches at least **k = 3** records, so **info_loss = 0**.

Use:
- `age = 22`
- `zip_code = 70001`

Expected:
- **success = true**
- **info_loss = 0**
- `generalized_data.zip_code` remains `70001`

### Scenario 2 — The Generalization Case (ZipCode masking with `*`)
Goal: not enough exact matches at first, so the system generalizes the ZipCode to reach **k = 3**.

Use:
- `age = 34`
- `zip_code = 70129`

Expected:
- Initially, `70129` is too specific (not enough people).
- System generalizes ZipCode to **`7012*`** to include nearby records (e.g., 70121, 70123, 70129).
- **success = true**
- **info_loss > 0**
- `generalized_data.zip_code` becomes **`7012*`**

### Scenario 3 — Fault Tolerance (Node Failure)
Goal: demonstrate anonymization still succeeds when one peer is down, by using timeouts + further generalization.

Steps:
1) Stop Node **8002** in its terminal:
   - Press **Ctrl + C**
2) On Node **8001** Swagger UI (`/docs`), call:
   - `age = 45`
   - `zip_code = 70300`

Expected:
- Node 8001 attempts to contact peers; Node 8002 times out and is counted as **0**.
- If the remaining nodes cannot reach **k = 3** with `70300`, the algorithm generalizes to **`7030*`** to include `70301`.
- **success = true**
- **info_loss > 0**
- `per_node_counts` shows Node 8002 as missing / 0 contribution.

---

## Quick Automated E2E Test (Optional)
If you want a fully automated demo:

```bash
python auto_test.py
```

It will:
- Start all 3 nodes in the background
- Run tests once with all nodes up
- Kill Node 8002 automatically
- Run tests again to show fault tolerance
- Always teardown remaining nodes to free ports

