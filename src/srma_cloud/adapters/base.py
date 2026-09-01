"""
Storage adapter interface.

Any cloud or local backend the screening pipeline talks to implements this
interface. v1 ships only `GoogleDriveAdapter`; the interface is deliberately
narrow (three methods) so a second backend (S3, GCS, OneDrive, local disk)
can be added without touching the ingestion, prompt, or decision-logging
layers. This is the piece of the architecture the methods paper should point
to when arguing the pipeline is "cloud-agnostic by design, Drive-validated
in this study."
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class FileRef:
    """A pointer to a single remote file, backend-agnostic."""

    id: str  # backend-native identifier (Drive fileId, S3 key, etc.)
    name: str  # display name, e.g. "smith2023.pdf"
    mime_type: str
    modified_time: str  # ISO 8601 string
    size_bytes: Optional[int] = None


@dataclass(frozen=True)
class ScreeningDecision:
    """The output of one screening pass on one file."""

    file_ref: FileRef
    stage: str  # "abstract" or "full_text"
    decision: str  # "include" | "exclude" | "uncertain"
    rationale: str
    model_name: str
    raw_output: str


class StorageAdapter(ABC):
    """Backend-agnostic interface for reading citations/PDFs and writing decisions."""

    @abstractmethod
    def list_new_files(self, folder_ref: str, since: Optional[str] = None) -> Iterable[FileRef]:
        """Return files in `folder_ref` that are new/modified since `since`.

        Implementations are responsible for their own pagination and for
        filtering to supported mime types (PDF, plain text, RIS/CSV export).
        """

    @abstractmethod
    def fetch_file(self, file_ref: FileRef) -> bytes:
        """Download raw file bytes for `file_ref`."""

    @abstractmethod
    def write_decision(self, decision: ScreeningDecision, destination_ref: str) -> None:
        """Persist a screening decision back to the backend.

        For Drive this is a row in a tracking Sheet (and optionally moving/
        tagging the source file); for other backends this might be a JSON
        sidecar object or a database write. The pipeline never needs to know
        which.
        """
