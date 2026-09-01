"""
Orchestrator: wires an adapter, the parser, the prompt engine, and decision
logging into one run. This is the piece that makes the tool "seamless" —
one call screens every new file in a watched folder and writes results back
without anyone downloading anything by hand.
"""

from __future__ import annotations

import logging
from typing import Optional

from .adapters.base import ScreeningDecision, StorageAdapter
from .ingestion.parser import parse
from .prompts.engine import ModelClient, extract_decision
from .prompts.templates import ReviewCriteria, build_abstract_prompt, build_full_text_prompt

log = logging.getLogger(__name__)


def run_full_text_screen(
    adapter: StorageAdapter,
    model_client: ModelClient,
    criteria: ReviewCriteria,
    source_folder_ref: str,
    log_destination_ref: str,
    since: Optional[str] = None,
) -> list[ScreeningDecision]:
    """Screens every new/updated full-text file in `source_folder_ref`.

    Files flagged as likely-scanned by the parser are skipped and should be
    routed to OCR or a human-review queue by the caller — screening a near-
    empty extraction would silently degrade sensitivity.
    """
    decisions: list[ScreeningDecision] = []

    for file_ref in adapter.list_new_files(source_folder_ref, since=since):
        raw = adapter.fetch_file(file_ref)
        doc = parse(raw, file_ref.mime_type)

        if doc.likely_scanned:
            log.warning("Skipping likely-scanned PDF (needs OCR): %s", file_ref.name)
            continue

        prompt = build_full_text_prompt(criteria, doc.text)
        response = model_client.complete(prompt)
        decision, rationale = extract_decision(response.raw_text)

        result = ScreeningDecision(
            file_ref=file_ref,
            stage="full_text",
            decision=decision,
            rationale=rationale,
            model_name=response.model_name,
            raw_output=response.raw_text,
        )
        adapter.write_decision(result, log_destination_ref)
        decisions.append(result)
        log.info("Screened %s -> %s", file_ref.name, decision)

    return decisions
