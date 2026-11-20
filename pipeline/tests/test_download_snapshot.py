"""Tests through the FactPages downloader, with a fake fetch instead of the network."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import date
from pathlib import Path

import pytest

from wildcat_pipeline import (
    DownloadError,
    NoSummaryWriter,
    build_well_proposals,
    download_snapshot,
    load_snapshot,
)

FIXTURE = Path(__file__).parent / "fixtures" / "snapshot"
BOM = b"\xef\xbb\xbf"


def zipped(name: str, content: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, content)
    return buffer.getvalue()


class FakeFactPages:
    """Serves the fixture snapshot the way FactPages does: CSV with a BOM,
    block outlines as a zipped CSV."""

    def __init__(self) -> None:
        self.requested: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.requested.append(url)
        if "blkArea" in url:
            return zipped("blkArea.csv", BOM + b'blcName,blkAreaGeometryWKT\r\n34/10,"POLYGON ((2 61,3 61,3 62,2 61))"\r\n')
        for name in ("wellbore_exploration_all", "discovery"):
            if f"/{name}&" in url:
                return BOM + (FIXTURE / f"{name}.csv").read_bytes()
        return BOM + b"name,npdid\r\nA,1\r\n"


def test_a_downloaded_snapshot_builds_the_same_dataset_as_the_files_served(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot"
    download_snapshot(snapshot, FakeFactPages())

    def build(directory: Path) -> object:
        return build_well_proposals(load_snapshot(directory), NoSummaryWriter(), build_date=date(2026, 11, 20))

    assert build(snapshot) == build(FIXTURE)


def test_download_saves_every_table_the_game_uses(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot"
    download_snapshot(snapshot, FakeFactPages())

    assert sorted(p.name for p in snapshot.iterdir()) == [
        "blkArea.csv",  # block outlines
        "discovery.csv",
        "field.csv",
        "licence.csv",
        "snapshot.json",
        "survey.csv",  # seismic surveys
        "wellbore_exploration_all.csv",
    ]
    assert "POLYGON" in (snapshot / "blkArea.csv").read_text(encoding="utf-8-sig")


def test_download_records_when_and_where_each_file_came_from(tmp_path: Path) -> None:
    fetch = FakeFactPages()
    snapshot = tmp_path / "snapshot"
    download_snapshot(snapshot, fetch)

    manifest = json.loads((snapshot / "snapshot.json").read_text(encoding="utf-8"))
    assert manifest["downloaded_at"].startswith(date.today().isoformat())
    assert sorted(manifest["files"].values()) == sorted(fetch.requested)
    assert all(url.startswith("https://factpages.sodir.no/") for url in fetch.requested)


def test_download_fails_on_an_error_page_and_leaves_no_snapshot(tmp_path: Path) -> None:
    def broken(url: str) -> bytes:
        if "/licence&" in url:
            return b"<html><head><title>SQL Server Reporting Services</title></head></html>"
        return FakeFactPages()(url)

    snapshot = tmp_path / "snapshot"
    with pytest.raises(DownloadError, match="licence"):
        download_snapshot(snapshot, broken)

    assert not snapshot.exists()
    assert list(tmp_path.iterdir()) == []


def test_download_never_overwrites_an_existing_snapshot(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    (snapshot / "wellbore_exploration_all.csv").write_text("kept", encoding="utf-8")

    with pytest.raises(FileExistsError):
        download_snapshot(snapshot, FakeFactPages())

    assert (snapshot / "wellbore_exploration_all.csv").read_text(encoding="utf-8") == "kept"
