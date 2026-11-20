"""Summary review: a sample of the summaries, for a person to read on each build.

The leak guard catches names and years, but not a summary that gives the
Outcome away in other words, or one that is hard to follow. Each sampled
summary is shown beside its Reveal, so the reader can judge both.
"""

from __future__ import annotations

import random
from typing import Any

REVIEW_SIZE = 20


def summary_review(dataset: dict[str, Any], *, size: int = REVIEW_SIZE) -> str:
    """A Markdown review of `size` sampled summaries and every flagged well.

    The sample is drawn from the dataset version, so the same dataset always
    gives the same review.
    """
    written = [p for p in dataset["well_proposals"] if p["dossier"]["summary"]]
    flagged = [p for p in dataset["well_proposals"] if not p["dossier"]["summary"]]
    sample = random.Random(dataset["dataset_version"]).sample(written, min(size, len(written)))

    lines = [
        f"# Summary review: dataset {dataset['dataset_version']}",
        "",
        "Read each summary beside its Reveal. It must not give the well, operator, year or",
        "Outcome away, even in other words, and it must make sense to a non-expert.",
        "",
        f"## Sample ({len(sample)} of {len(written)} summaries)",
    ]
    for well_proposal in sample:
        dossier, reveal = well_proposal["dossier"], well_proposal["reveal"]
        lines += [
            "",
            f"### {reveal['well_name']} ({reveal['outcome']}, {reveal['year']})",
            "",
            f"Block {dossier['block']}, {dossier['decade']}",
            "",
            f"> {dossier['summary']}",
        ]
    lines += ["", f"## Flagged: no summary ({len(flagged)})", ""]
    lines += [f"- {p['reveal']['well_name']} ({p['id']})" for p in flagged] or ["None."]
    return "\n".join(lines) + "\n"
