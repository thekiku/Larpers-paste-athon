# Adaptive Queue Intelligence System (AQIS)

Python backend for a dynamic priority queue using lazy updates and versioning.

## Features

- Max-heap priority queue behavior built on top of `heapq`
- Scoring function:
  - `score = alpha * urgency + gamma * categoryWeight - beta * arrivalTime`
- Lazy updates for priority changes
- Version map to discard stale heap entries
- Arrival timestamp fairness with no in-place heap mutation
- In-memory runtime (no database)

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
