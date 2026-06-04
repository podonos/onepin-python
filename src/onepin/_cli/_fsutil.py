"""Shared filesystem helper: atomic write with an optional clobber guard.

The idiom — reserve the destination with ``O_CREAT|O_EXCL`` when not overwriting, then write
to a temp file in the same directory and ``os.replace`` it into place — is subtle (it closes
a TOCTOU window and respects Windows' "no open handle during replace" rule), so it lives here
once and is shared by the run-download composites and ``onepin skill install``. Callers map the
raised builtin exceptions to their own stable error codes.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_bytes(dest: Path, content: bytes, *, force: bool) -> None:
    """Write ``content`` to ``dest`` atomically.

    When ``force`` is False the destination is reserved via ``O_CREAT|O_EXCL`` so a file that
    appears between an external existence check and the rename is never silently clobbered.

    Raises:
        FileExistsError: ``force`` is False and ``dest`` already exists.
        FileNotFoundError | NotADirectoryError: the parent directory does not exist.
        OSError: any other write failure.
    """
    parent = dest.parent

    # Atomically claim the destination so a file created after the caller's pre-check is not
    # clobbered. Close the handle immediately: the empty placeholder stays as the guard, and
    # os.replace() can overwrite it only when no handle is open (Windows raises otherwise).
    reserved = False
    if not force:
        fd = os.open(str(dest), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        reserved = True

    try:
        tmp_fd, tmp_name = tempfile.mkstemp(dir=str(parent) if str(parent) else ".", prefix=".onepin-tmp-")
    except OSError:
        if reserved:
            try_unlink(dest)
        raise
    try:
        with os.fdopen(tmp_fd, "wb") as handle:
            handle.write(content)
        os.replace(tmp_name, dest)
    except OSError:
        try_unlink(tmp_name)
        if reserved:
            try_unlink(dest)
        raise


def try_unlink(path: Path | str) -> None:
    """Best-effort unlink that never raises (used to clean up reservations / temp files)."""
    try:
        os.unlink(path)
    except OSError:
        pass
