"""
Exercises the pipeline against fake adapter/model implementations so it
never needs live Drive or LLM credentials.
"""

from srma_cloud.adapters.base import FileRef, ScreeningDecision, StorageAdapter
from srma_cloud.pipeline import FULL_TEXT_MAX_TOKENS, run_abstract_screen, run_full_text_screen
from srma_cloud.prompts.engine import ModelClient, ModelResponse
from srma_cloud.prompts.templates import ReviewCriteria

CRITERIA = ReviewCriteria(
    objectives="Evaluate X.",
    inclusion_criteria=["Population: adults"],
    exclusion_criteria=["Not in English"],
)


class RecordingModelClient(ModelClient):
    """Returns a fixed decision and records the max_tokens it was called with."""

    def __init__(self, decision_line: str = "DECISION: INCLUDE"):
        self.calls: list[int] = []
        self._decision_line = decision_line

    def complete(self, prompt: str, max_tokens: int = 1024) -> ModelResponse:
        self.calls.append(max_tokens)
        return ModelResponse(raw_text=f"Reasoning...\n{self._decision_line}", model_name="fake-model")


class FakeAdapter(StorageAdapter):
    def __init__(self, files: dict[str, bytes]):
        self._files = files
        self.written: list[ScreeningDecision] = []

    def list_new_files(self, folder_ref, since=None):
        for name, content in self._files.items():
            yield FileRef(id=name, name=name, mime_type="text/plain", modified_time="2026-01-01T00:00:00Z")

    def fetch_file(self, file_ref):
        return self._files[file_ref.id]

    def write_decision(self, decision, destination_ref):
        self.written.append(decision)


def test_full_text_screen_uses_higher_max_tokens():
    adapter = FakeAdapter({"a.txt": b"some article text"})
    model = RecordingModelClient()

    decisions = run_full_text_screen(adapter, model, CRITERIA, "folder", "sheet")

    assert len(decisions) == 1
    assert decisions[0].decision == "include"
    assert decisions[0].stage == "full_text"
    assert model.calls == [FULL_TEXT_MAX_TOKENS]
    assert adapter.written == decisions


def test_abstract_screen_round_trip():
    adapter = FakeAdapter({})
    model = RecordingModelClient(decision_line="DECISION: EXCLUDE")
    citations = [
        (FileRef(id="c1", name="c1", mime_type="text/plain", modified_time="2026-01-01T00:00:00Z"), "Title", "Abstract text"),
    ]

    decisions = run_abstract_screen(adapter, model, CRITERIA, citations, "sheet")

    assert len(decisions) == 1
    assert decisions[0].decision == "exclude"
    assert decisions[0].stage == "abstract"
    assert adapter.written == decisions
