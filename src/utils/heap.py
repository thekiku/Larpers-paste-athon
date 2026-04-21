import heapq
from dataclasses import dataclass
from typing import List, Tuple

from src.models.queue_entry import QueueEntry


@dataclass(slots=True)
class HeapItem:
    sort_key: Tuple[float, int, int]
    entry: QueueEntry


class MaxHeap:
    def __init__(self) -> None:
        self._heap: List[HeapItem] = []

    def push(self, entry: QueueEntry, sequence: int) -> None:
        # heapq is a min-heap, so we negate score to simulate max-heap behavior.
        item = HeapItem(sort_key=(-entry.score, entry.arrival_time_ms, sequence), entry=entry)
        heapq.heappush(self._heap, item)

    def pop(self) -> QueueEntry:
        item = heapq.heappop(self._heap)
        return item.entry

    def copy_heap(self) -> list[HeapItem]:
        return list(self._heap)

    def __len__(self) -> int:
        return len(self._heap)
