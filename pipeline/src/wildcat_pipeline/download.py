"""FactPages downloader: saves a fresh FactPages snapshot to local files.

Run by hand, and kept apart from processing: the pipeline only ever reads a
snapshot directory, so tests can use the hand-made fixture instead.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

Fetch = Callable[[str], bytes]

_TABLE_URL = (
    "https://factpages.sodir.no/public?/Factpages/external/tableview/{table}"
    "&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used"
    "&CultureCode=en&rs:Format=CSV&Top100=false"
)


@dataclass(frozen=True)
class Source:
    """One file of a snapshot and where FactPages publishes it."""

    file: str
    url: str
    zipped: bool = False  # spatial data comes as a zipped CSV with WKT geometry


def _table(name: str) -> Source:
    return Source(f"{name}.csv", _TABLE_URL.format(table=name))


# The build reads the first two so far; the rest are for the Hints and the map.
SOURCES = [
    _table("wellbore_exploration_all"),  # wellbores
    _table("discovery"),
    _table("field"),
    _table("licence"),
    _table("survey"),  # seismic surveys
    Source("blkArea.csv", "https://factpages.sodir.no/downloads/csv/blkArea.zip", zipped=True),  # block outlines
]

MANIFEST_FILE = "snapshot.json"


class DownloadError(Exception):
    """FactPages did not return the data the snapshot needs."""


def download_snapshot(directory: Path | str, fetch: Fetch | None = None) -> None:
    """Download a FactPages snapshot into `directory`, which must not exist yet.

    The snapshot appears all at once: if any file fails, nothing is left
    behind. A snapshot.json manifest records when and from where each file
    came.
    """
    directory = Path(directory)
    fetch = fetch or fetch_url
    if directory.exists():
        raise FileExistsError(f"{directory} already exists; snapshots are never overwritten")

    directory.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(tempfile.mkdtemp(prefix=f".{directory.name}.", dir=directory.parent))
    partial.chmod(0o755)  # mkdtemp makes it private to the user
    try:
        for source in SOURCES:
            content = fetch(source.url)
            _save_checked_csv(partial, source, _unzip(content, source) if source.zipped else content)
        manifest = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "files": {source.file: source.url for source in SOURCES},
        }
        (partial / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        partial.rename(directory)
    except BaseException:
        shutil.rmtree(partial, ignore_errors=True)
        raise


def fetch_url(url: str) -> bytes:
    """Fetch a URL over HTTPS. Raises on any HTTP error status."""
    request = urllib.request.Request(url, headers={"User-Agent": "wildcat-pipeline"})
    with urllib.request.urlopen(request, timeout=600) as response:
        body: bytes = response.read()
        return body


def _save_checked_csv(directory: Path, source: Source, content: bytes) -> None:
    # FactPages reports errors as an HTML page, sometimes with status 200.
    header = content.removeprefix(b"\xef\xbb\xbf").split(b"\n", 1)[0]
    if header.lstrip().startswith(b"<") or b"," not in header:
        raise DownloadError(f"{source.file}: {source.url} did not return a CSV table")
    (directory / source.file).write_bytes(content)


def _unzip(archive: bytes, source: Source) -> bytes:
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as opened:
            return opened.read(source.file)
    except (zipfile.BadZipFile, KeyError) as error:
        raise DownloadError(f"{source.file}: {source.url} did not return a zip holding {source.file}") from error
