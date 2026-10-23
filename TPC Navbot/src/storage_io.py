"""Atomic text-file publication for overlapping application initializers."""
from contextlib import contextmanager
import os
from pathlib import Path
import tempfile
import time


def _replace_file(temporary, destination):
    # Windows readers/scanners can briefly block replacement with sharing, lock,
    # or access-denied errors. Retry these for at most 0.62 seconds of backoff;
    # persistent permissions failures still propagate, preserving their cause.
    for attempt in range(6):
        try:
            os.replace(temporary, destination)
            return
        except OSError as exc:
            if getattr(exc, "winerror", None) not in {5, 32, 33} or attempt == 5:
                raise
            time.sleep(0.02 * (2 ** attempt))


@contextmanager
def atomic_text_writer(destination):
    """Publish a complete UTF-8 file using a private, same-directory temporary.

    Each writer owns its temporary path. Closing it before replacement is also
    required on Windows. Overlapping writers may publish in either order, but
    readers never see a partially written file or another writer's temporary.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=destination.parent,
                prefix=f".{destination.name}.", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            yield output
        _replace_file(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def atomic_write_text(destination, text):
    with atomic_text_writer(destination) as output:
        output.write(text)
