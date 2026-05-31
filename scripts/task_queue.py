"""
task_queue.py — minimal persistent tracker for in-flight Seedance tasks.

WHY:
  Stage 4 submits to BytePlus and then polls for up to 15 min per video.
  If Streamlit drops the connection (replica swap, network blip, browser refresh)
  during the long poll, the script restarts and re-submits the same prompt from
  scratch — paying for video #1 again instead of collecting the one already done.

FIX:
  After each submit_task → add_task() writes {task_id, video_id, chunk_idx, ...}
  to a JSON file on disk. After download → mark_done() removes it. On Stage 4
  entry, get_pending() returns any unfinished tasks so the UI can offer
  'Resume N pending' before submitting anything new.

  File: outputs/_tasks.json
  Schema: list of dicts. Each dict =
    {
      task_id: str,         # BytePlus task id (cgt-...)
      video_id: int|str,    # which logical video this is for
      chunk_idx: int,       # 1, 2, 3 ... (for multi-chunk videos)
      total_chunks: int,    # how many chunks total for this video
      prompt: str,          # the prompt that was submitted (for reference)
      submitted_at: float,  # unix timestamp
      duration: int,        # seconds
      aspect_ratio: str,
      done: bool,           # True after download succeeded
      output_path: str|None,
    }
"""

import json
import os
import time
from pathlib import Path
from typing import Optional


def _state_path() -> Path:
    """Where the JSON state file lives. Always inside outputs/."""
    here = Path(__file__).resolve().parent.parent
    p = here / "outputs" / "_tasks.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load() -> list:
    p = _state_path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(tasks: list) -> None:
    p = _state_path()
    p.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")


def add_task(
    task_id: str,
    video_id,
    chunk_idx: int = 1,
    total_chunks: int = 1,
    prompt: str = "",
    duration: int = 15,
    aspect_ratio: str = "9:16",
) -> None:
    """Record a freshly-submitted task. Called immediately after submit_task succeeds."""
    tasks = _load()
    # If somehow this task_id already exists, update instead of duplicating
    for t in tasks:
        if t.get("task_id") == task_id:
            t.update({
                "video_id": video_id, "chunk_idx": chunk_idx,
                "total_chunks": total_chunks, "prompt": prompt[:500],
                "duration": duration, "aspect_ratio": aspect_ratio,
            })
            _save(tasks)
            return
    tasks.append({
        "task_id": task_id,
        "video_id": video_id,
        "chunk_idx": chunk_idx,
        "total_chunks": total_chunks,
        "prompt": prompt[:500],  # truncate to keep file small
        "submitted_at": time.time(),
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "done": False,
        "output_path": None,
    })
    _save(tasks)


def mark_done(task_id: str, output_path: Optional[str] = None) -> None:
    """Mark a task as completed and store the local file path."""
    tasks = _load()
    for t in tasks:
        if t.get("task_id") == task_id:
            t["done"] = True
            if output_path:
                t["output_path"] = str(output_path)
            break
    _save(tasks)


def get_pending(min_age_seconds: int = 0) -> list:
    """Return all tasks that are not yet done.

    Args:
      min_age_seconds: skip tasks submitted less than this many seconds ago.
        Useful to avoid racing with a still-running submit.
    """
    now = time.time()
    return [
        t for t in _load()
        if not t.get("done")
        and (now - t.get("submitted_at", 0)) >= min_age_seconds
    ]


def remove_done_older_than(days: int = 7) -> int:
    """Drop completed tasks older than `days`. Returns count removed."""
    cutoff = time.time() - (days * 86400)
    tasks = _load()
    keep = [t for t in tasks if not (t.get("done") and t.get("submitted_at", 0) < cutoff)]
    removed = len(tasks) - len(keep)
    if removed:
        _save(keep)
    return removed


def clear_all() -> None:
    """Wipe the queue. Use sparingly — e.g. from a 'reset' button in the UI."""
    p = _state_path()
    if p.exists():
        p.unlink()


def stats() -> dict:
    """Quick summary: {pending: N, done: M, total: N+M}."""
    tasks = _load()
    pending = sum(1 for t in tasks if not t.get("done"))
    done = sum(1 for t in tasks if t.get("done"))
    return {"pending": pending, "done": done, "total": len(tasks)}
