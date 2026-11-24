"""Crash-safe local file writes shared by campus business modules."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import weakref
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from campus_core.empty_classroom.lock import FileLock


_LOCKS_GUARD = threading.Lock()
_PROCESS_LOCKS: weakref.WeakValueDictionary[Path, threading.RLock] = (
    weakref.WeakValueDictionary()
)
_TRANSACTION_STATE = threading.local()


def _process_lock(path: Path) -> threading.RLock:
    with _LOCKS_GUARD:
        return _PROCESS_LOCKS.setdefault(path, threading.RLock())


@contextmanager
def file_transaction(
    target: str | os.PathLike[str],
    *,
    timeout: float = 30.0,
    stale_after: float = 3600.0,
) -> Iterator[None]:
    """Serialize a read-modify-write domain across threads and processes."""
    deadline = time.monotonic() + timeout
    lock_path = Path(f"{Path(target).resolve()}.lock")
    held_paths = getattr(_TRANSACTION_STATE, "held_paths", None)
    if held_paths is None:
        held_paths = _TRANSACTION_STATE.held_paths = set()
    if lock_path in held_paths:
        yield
        return

    process_lock = _process_lock(lock_path)
    remaining = deadline - time.monotonic()
    if remaining <= 0 or not process_lock.acquire(timeout=remaining):
        raise TimeoutError(f"file transaction lock timed out: {lock_path}")
    try:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"file transaction lock timed out: {lock_path}")
        lock = FileLock(lock_path, timeout=remaining, stale_after=stale_after)
        if not lock.acquire():
            raise TimeoutError(f"file transaction lock timed out: {lock_path}")
        try:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"file transaction lock timed out: {lock_path}")
            held_paths.add(lock_path)
            try:
                yield
            finally:
                held_paths.remove(lock_path)
        finally:
            lock.release()
    finally:
        process_lock.release()


def _fsync_directory(directory: Path) -> None:
    """Persist a completed rename when the platform supports directory fsync."""
    try:
        directory_fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def atomic_write_text(path: str | os.PathLike[str], text: str, *, encoding: str = "utf-8") -> None:
    """Durably replace ``path`` using a private temporary file beside it."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as stream:
            fd = -1
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def atomic_write_json(path: str | os.PathLike[str], value: Any) -> None:
    """Serialize JSON and replace its destination atomically."""
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2),
    )


__all__ = ["atomic_write_json", "atomic_write_text", "file_transaction"]
