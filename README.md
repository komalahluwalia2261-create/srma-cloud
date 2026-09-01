# srma-cloud

Cloud-native LLM screening for systematic reviews. Point it at a watched
Drive folder; it screens new PDFs against your review's eligibility
criteria and writes decisions back to a shared tracking sheet — no manual
export/upload cycle.

Built to close a gap in existing screening tools (Rayyan, Abstrackr,
RobotAnalyst, ASReview, AiReview, and the prompt-engineering work of
[Cao et al., 2025](https://doi.org/10.7326/ANNALS-24-02189)), all of which
require citations to be manually exported and uploaded rather than read
directly from cloud storage. See [`docs/architecture.md`](docs/architecture.md)
for the design rationale and evaluation plan, and [`paper/`](paper/) for
the accompanying methods manuscript in progress.

## Status

Early-stage / research scaffold. The Google Drive backend is implemented;
the architecture is designed so additional backends (S3, GCS, OneDrive,
local disk) can be added by implementing `StorageAdapter` — see
`src/srma_cloud/adapters/base.py`.

## Install

```bash
git clone <this-repo>
cd srma-cloud
python -m venv .venv && source .venv/bin/activate
pip install -e ".[anthropic,dev]"   # or [openai,dev]
```

## Set up Google Drive access

1. In [Google Cloud Console](https://console.cloud.google.com/), create a
   project, enable the **Drive API** and **Sheets API**, and create an
   OAuth 2.0 Client ID (Desktop app type).
2. Download the client secrets JSON, save as `client_secrets.json` in the
   repo root (already gitignored).
3. Create a Drive folder to hold candidate PDFs, and a Sheet to log
   decisions (header row: `file_id | file_name | stage | decision |
   rationale | model | modified_time`). Share both with your Google
   account if not already owned by it.
4. Set your model API key:
   ```bash
   export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY
   ```

## Define your review criteria

Copy `config/example_review.yaml` and edit `objectives`,
`inclusion_criteria`, and `exclusion_criteria` — insert them **verbatim**
from your protocol; do not paraphrase (see `docs/architecture.md` for why).

## Run

```bash
srma-cloud screen \
  --config config/my_review.yaml \
  --source-folder <drive_folder_id> \
  --log-sheet <spreadsheet_id> \
  --backend anthropic \
  -v
```

The first run authenticates via your browser (OAuth) and caches a token
locally. Re-running with `--since <ISO timestamp>` screens only files
modified after that point, so it's safe to re-run as new PDFs land in the
folder.

## Repository layout

```
src/srma_cloud/
  adapters/       StorageAdapter interface + Google Drive implementation
  ingestion/      PDF/text parsing, scanned-PDF detection, hashing
  prompts/        Prompt templates + model-agnostic call layer
  pipeline.py     Orchestrates adapter -> parser -> prompts -> decision log
  cli.py          Command-line entrypoint
config/           Example review-criteria YAML
docs/             Architecture and design rationale
paper/            Draft methods manuscript
tests/            Unit tests (run against a fake in-memory adapter, no
                  network/credentials required)
```

## Testing

```bash
pytest tests/ -v
```

## Contributing

Issues and PRs welcome, particularly additional `StorageAdapter`
backends and evaluation results on other benchmark review sets.

## License

MIT — see `LICENSE`.

## Citation

If you use this tool, please cite the accompanying methods paper (in
preparation; citation to be added) and the prior work this builds on:

> Cao C, Sang J, Arora R, et al. Development of Prompt Templates for Large
> Language Model–Driven Screening in Systematic Reviews. *Ann Intern Med*.
> 2025;178:389-401. doi:10.7326/ANNALS-24-02189
