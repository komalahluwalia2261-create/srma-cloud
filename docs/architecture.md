# Architecture

## Design goal

Existing LLM-assisted screening tools (Rayyan, Abstrackr, RobotAnalyst,
ASReview, AiReview, and the BenchSR/ScreenPrompt work of Cao et al., 2025)
operate on citation files a reviewer exports and uploads by hand. None
reads directly from a live cloud folder. For a review team that adds PDFs
to a shared Drive folder as the search is run, this means a manual
export/upload cycle every time the pool of candidate articles changes.

`srma-cloud` closes that loop: point it at a folder, it screens whatever is
new since the last run, and writes decisions back to a shared tracking
sheet — no local download step.

## Storage adapter pattern

The pipeline never touches a cloud SDK directly. Every backend implements
`StorageAdapter` (`adapters/base.py`):

- `list_new_files(folder_ref, since)`
- `fetch_file(file_ref)`
- `write_decision(decision, destination_ref)`

`GoogleDriveAdapter` is the only implementation shipped in v1. A second
backend (S3, GCS, OneDrive, local disk for offline use) is a matter of
implementing these three methods — nothing in `ingestion/`, `prompts/`, or
`pipeline.py` is Drive-specific. This is the architectural claim the
methods paper should evaluate empirically: that wrapping screening in this
I/O layer does not change sensitivity/specificity relative to a
file-upload-based pipeline run on the same criteria and model.

## Prompt design

Prompt structure follows patterns reported in the literature to matter for
criteria-based screening tasks (not any single paper's exact wording):

- Eligibility criteria inserted **verbatim** from the review protocol,
  numbered per-subcriterion rather than grouped under headers like
  "Population" / "Study design" — reported to reduce omission errors.
- Explicit step-by-step reasoning against each criterion before a decision
  token, rather than a bare include/exclude request.
- For full-text screening, criteria and instructions are repeated both
  before and after the article body, to counter the documented tendency of
  LLMs to under-attend to instructions placed once at the start of a long
  context ("lost in the middle").

See `prompts/templates.py` for the implementation and inline citations to
the specific findings each choice is based on.

## Evaluation plan

To make the "doesn't hurt accuracy" claim credible, the pipeline should be
run against a public benchmark with a known reference standard rather than
only the reviews it was built for. BenchSR (Cao et al., 2025;
github.com/JZSang/srma) is the natural choice: 10 systematic reviews with
full citation pools and author-verified include/exclude decisions,
directly comparable sensitivity/specificity numbers already published for
zero-shot and optimized prompting baselines.

Planned comparison arms:
1. Zero-shot prompting (lower bound, per Cao et al.)
2. File-upload pipeline reproducing Abstract ScreenPrompt / ISO-ScreenPrompt
   (reproduction of the published baseline)
3. `srma-cloud` end-to-end (same prompts, routed through the storage
   adapter) — the arm that tests whether the added I/O layer changes
   performance

## Known limitations to design around

- **Scanned PDFs**: `ingestion/parser.py` flags low-text-yield PDFs rather
  than screening on a near-empty extraction. These need OCR or human
  triage; silently screening them would look like a sensitivity drop that
  is actually a parsing failure, not a model failure.
- **Full-text paywall coverage**: Cao et al. found only ~7.6% of citations
  in their pooled search had freely available full text. A Drive-based
  pipeline doesn't solve this — it still needs someone (or an institutional
  proxy/API) to have put the PDF in the folder. Worth stating explicitly as
  a limitation rather than implying cloud access solves retrieval.
- **Drive API quotas**: default quota is generous for review-scale folders
  (hundreds to low thousands of files) but polling frequency and file
  count should be kept in mind for very large searches.
