"""Run the pipeline by hand: snapshot directory in, prospects.json out."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .build import build_prospects, log
from .snapshot import load_snapshot
from .summary import NoSummaryWriter


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="wildcat-pipeline", description=__doc__)
    parser.add_argument("snapshot", type=Path, help="directory of FactPages CSV exports")
    parser.add_argument("output", type=Path, help="where to write prospects.json")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    dataset = build_prospects(load_snapshot(args.snapshot), NoSummaryWriter())
    args.output.write_text(json.dumps(dataset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log.info(
        "Wrote %d Prospects, version %s, to %s",
        len(dataset["prospects"]),
        dataset["dataset_version"],
        args.output,
    )
