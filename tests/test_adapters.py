"""
Tests run against a fake in-memory StorageAdapter, not live Google Drive —
this keeps CI free of network calls and credentials while still exercising
the interface contract every real backend must satisfy.
"""

from srma_cloud.adapters.base import FileRef, ScreeningDecision, StorageAdapter


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


def test_fake_adapter_round_trip():
    adapter = FakeAdapter({"a.txt": b"hello world"})
    refs = list(adapter.list_new_files("any_folder"))
    assert len(refs) == 1
    assert adapter.fetch_file(refs[0]) == b"hello world"

    decision = ScreeningDecision(
        file_ref=refs[0],
        stage="full_text",
        decision="include",
        rationale="meets all criteria",
        model_name="test-model",
        raw_output="DECISION: INCLUDE",
    )
    adapter.write_decision(decision, "dest")
    assert adapter.written == [decision]
