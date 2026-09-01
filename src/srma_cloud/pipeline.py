"""
Orchestrator: wires an adapter, the parser, the prompt engine, and decision
logging into one run. This is the piece that makes the tool "seamless" —
one call screens every new file in a watched folder and writes results back
without anyone downloading anything by hand.
"""

from __future__ import annotations

import logging
from typing import Optional

from .adapters.base import FileRef, ScreeningDecision, StorageAdapter
from .ingestion.parser import parse
from .prompts.engine import ModelClient, extract_decision
from .prompts.templates import ReviewCriteria, build_abstract_prompt, build_full_text_prompt

log = logging.getLogger(__name__)

# Full-text reasoning walks every criterion twice (once per repeated
# instruction block) and cites supporting text for each — the default
# max_tokens=1024 on ModelClient.complete truncates this before the
# required "DECISION:" line, which extract_decision then silently reads
# as "uncertain". Abstracts are short, so 1024 is fine for that stage.
FULL_TEXT_MAX_TOKENS = 4096


def run_abstract_screen(
    adapter: StorageAdapter,
    model_client: ModelClient,
    criteria: ReviewCriteria,
    citations: list[tuple[FileRef, str, str]],
    log_destination_ref: str,
) -> list[ScreeningDecision]:
    """Screens a list of (file_ref, title, abstract) citations at the abstract stage.

    Unlike `run_full_text_screen`, citations are passed in directly rather
    than listed from the adapter — abstract screening runs against a
    citation export (e.g. a benchmark's title/abstract pool), not files
    sitting in a watched folder.
    """
    decisions: list[ScreeningDecision] = []

    for file_ref, title, abstract in citations:
        prompt = build_abstract_prompt(criteria, title, abstract)
        response = model_client.complete(prompt)
        decision, rationale = extract_decision(response.raw_text)

        result = ScreeningDecision(
            file_ref=file_ref,
            stage="abstract",
            decision=decision,
            rationale=rationale,
            model_name=response.model_name,
            raw_output=response.raw_text,
        )
        adapter.write_decision(result, log_destination_ref)
        decisions.append(result)
        log.info("Screened %s -> %s", file_ref.name, decision)

    return decisions


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
        response = model_client.complete(prompt, max_tokens=FULL_TEXT_MAX_TOKENS)
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
