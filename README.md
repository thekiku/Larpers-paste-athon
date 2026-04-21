# Adaptive Queue Intelligence System (AQIS)

AQIS is a backend-driven dynamic priority queue system.

## Topic and Algorithm Idea

- We use a priority-based queue system to dynamically order users based on a computed score.
- Each user is assigned a score calculated from urgency, category weight, and arrival time.
- Instead of explicitly tracking waiting time, we use arrival time in the scoring function.
- This lets priority evolve fairly over time without continuous recomputation.

- Instead of updating priorities in-place, the system uses a lazy update strategy:
  - Whenever a user's priority changes, a new updated entry is inserted into the queue.
  - Older entries are ignored when retrieved.

## Scoring Function

Score is computed as:

`score = alpha * urgency + gamma * categoryWeight - beta * arrivalTime`

### Where

- `urgency` represents the immediate importance of the user.
- `categoryWeight` represents system-defined priority (for example VIP or emergency).
- `arrivalTime` is the timestamp when the user entered the system.
- `alpha`, `beta`, `gamma` are tunable constants.

Since current time increases uniformly for all users, subtracting arrival time ensures users who have waited longer naturally gain higher priority.

## Data Structures

- Priority Queue (Max Heap behavior over `heapq`)
- Hash map for latest version tracking

## Queue Entry

Each entry contains:

- `user_id`
- `user_name`
- `score`
- `arrivalTime`
- `version`

## Core Operations

### 1. Insert User

- Set `arrivalTime = current timestamp`
- Compute score
- Set/initialize version
- Push entry into heap

Time complexity: `O(log n)`

### 2. Update User Priority (Lazy Update)

- Recompute score with updated urgency/category weight (arrival time remains unchanged)
- Increment version
- Push new entry into heap
- Older versions become stale

Time complexity: `O(log n)`

### 3. Extract Highest Priority User

- Pop from heap
- Validate entry against latest version map
- If outdated, discard and continue

Time complexity: `O(log n)` amortized

## Complexity Summary

- Insert: `O(log n)`
- Update: `O(log n)`
- Extract: `O(log n)`
- Space: `O(n)`

## Implementation (Current Project)

Python FastAPI backend for AQIS with API endpoints and modular service design.

## Features

- Max-heap priority queue behavior built on top of `heapq`
- Scoring function:
  - `score = alpha * urgency + gamma * categoryWeight - beta * arrivalTime`
- Lazy updates for priority changes
- Version map to discard stale heap entries
- Arrival timestamp fairness with no in-place heap mutation
- SQLite-backed persistence (`aqis.db`) for active user state

## Project Structure

```text
.
├── src
│   ├── app.py
│   ├── server.py
│   ├── config
│   │   └── settings.py
│   ├── controllers
│   │   └── queue_controller.py
│   ├── models
│   │   ├── queue_entry.py
│   │   └── schemas.py
│   ├── routes
│   │   └── queue_routes.py
│   ├── services
│   │   └── aqis_service.py
│   └── utils
│       └── heap.py
├── requirements.txt
└── README.md
```

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start server:

```bash
python -m src.server
```

Server starts at `http://127.0.0.1:8000`.

## API Endpoints

- `POST /user` add a user
- `PUT /user/{id}` update urgency/category weight (lazy update)
- `GET /queue` return full ordered active queue
- `GET /next` extract highest-priority user
- `GET /health` simple health check

## Sample Requests

### Add user

```bash
curl -X POST http://127.0.0.1:8000/user \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","urgency":8,"category_weight":5}'
```

### Update user

```bash
curl -X PUT http://127.0.0.1:8000/user/u1 \
  -H "Content-Type: application/json" \
  -d '{"urgency":10}'
```

### View queue

```bash
curl http://127.0.0.1:8000/queue
```

### Extract next

```bash
curl http://127.0.0.1:8000/next
```
