"""Run the pipeline by hand.

  download SNAPSHOT          save a fresh FactPages snapshot to a new directory
  build SNAPSHOT OUTPUT      turn a snapshot into well_proposals.json
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .build import build_well_proposals, log
from .download import download_snapshot
from .snapshot import load_snapshot
from .summary import NoSummaryWriter


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="wildcat-pipeline", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)

    download = commands.add_parser("download", help="save a fresh FactPages snapshot")
    download.add_argument("snapshot", type=Path, help="new directory to save the snapshot in")

    build = commands.add_parser("build", help="build well_proposals.json from a snapshot")
    build.add_argument("snapshot", type=Path, help="directory of FactPages CSV exports")
    build.add_argument("output", type=Path, help="where to write well_proposals.json")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.command == "download":
        _download(args.snapshot)
    else:
        _build(args.snapshot, args.output)


def _download(snapshot: Path) -> None:
    log.info("Downloading a FactPages snapshot to %s (this takes a minute or two)", snapshot)
    download_snapshot(snapshot)
    log.info("Saved the FactPages snapshot to %s", snapshot)


def _build(snapshot: Path, output: Path) -> None:
    dataset = build_well_proposals(load_snapshot(snapshot), NoSummaryWriter())
    output.write_text(json.dumps(dataset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log.info(
        "Wrote %d Well Proposals, version %s, to %s",
        len(dataset["well_proposals"]),
        dataset["dataset_version"],
        output,
    )
