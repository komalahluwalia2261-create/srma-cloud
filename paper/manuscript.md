# [Working title] A Cloud-Native Pipeline for LLM-Driven Systematic Review Screening: Design, Implementation, and Benchmark Evaluation

*Draft skeleton — structured to mirror Cao et al. (2025, Ann Intern Med)
for a methods/tools submission. Bracketed items are placeholders to fill
in once the tool is built and evaluated; section order and headers follow
that paper's structured-abstract + IMRaD convention as a starting point —
adjust to the target journal's actual requirements before submission.*

---

## Structured Abstract

**Background:** Large language models can screen systematic review (SR)
citations with sensitivity and specificity approaching that of human
reviewers when given well-engineered prompts. However, existing
screening tools — both classical active-learning tools (Rayyan,
Abstrackr, RobotAnalyst, ASReview) and recent LLM-based approaches —
operate on citation files exported and uploaded by hand, requiring a
manual retrieval-and-upload cycle each time the candidate pool changes.

**Objective:** To design, implement, and evaluate an open-source
screening pipeline that reads candidate citations and full texts directly
from a watched cloud storage folder and writes screening decisions back
to a shared log, without a manual export/upload step, and to test whether
this added infrastructure layer preserves screening sensitivity and
specificity relative to established file-upload-based baselines.

**Design:** [Diagnostic test accuracy / tool evaluation — confirm design
once evaluation is run.]

**Setting:** [Benchmark dataset(s) used — e.g., BenchSR (Cao et al.,
2025) plus/or your own in-progress reviews. Specify N citations, N
reviews.]

**Participants:** None (automated screening evaluated against
author-verified reference decisions).

**Measurements:** Accuracy, sensitivity, and specificity of pipeline
decisions against the reference standard (original review authors'
final include/exclude decisions), compared across: (1) zero-shot
prompting, (2) file-upload reproduction of an established optimized
prompt template, and (3) the cloud-native pipeline using the same
prompt template. Wall-clock time and direct cost per review, compared
with published human-reviewer estimates.

**Results:** [To be completed.]

**Limitations:** [To be completed — anticipate: full-text coverage
limited to what is placed in the watched folder; scanned-PDF handling;
single cloud backend evaluated in this study despite an
adapter-based design intended to generalize; convenience sample of
benchmark reviews.]

**Conclusion:** [To be completed.]

**Primary Funding Source:** [None / grant details.]

---

## 1. Introduction

Systematic reviews (SRs) remain resource-intensive largely because of
the screening phase, which requires two reviewers working independently
across title/abstract and full-text stages (Cumpston et al., 2019; Borah
et al., 2017). Large language models have recently been shown to
approach or exceed single-reviewer performance on this task when given
carefully engineered, criteria-specific prompts rather than naive
zero-shot instructions (Cao et al., 2025; Guo et al., 2024; Tran et al.,
2024). This has produced a growing set of open tools for LLM-assisted
screening (Rayyan, Abstrackr, RobotAnalyst, ASReview LAB v2, AiReview).

A workflow gap remains, however, upstream of the prompting problem: every
tool we are aware of screens citation files a reviewer exports from a
reference manager (RIS/CSV) and uploads by hand, and full-text screening
tools that go beyond this typically rely on a specific API for retrieval
(e.g., the PubMed Central BioC API used by Cao et al., 2025) rather than
a review team's own working storage. For teams that collect candidate
PDFs into a shared Drive (or other cloud) folder as searches and hand
searches are run — a common practice — this means repeating an
export/upload cycle every time the candidate pool changes, and it means
existing tools cannot screen material a team has already retrieved and
organized in their own cloud workspace.

This paper describes `srma-cloud`, an open-source pipeline that (1)
reads new or updated candidate files directly from a watched cloud
storage folder, (2) screens them using prompt templates built on
patterns reported to improve criteria-based LLM screening performance,
and (3) writes decisions back to a shared tracking log for human
adjudication — closing the retrieval-to-screening loop without manual
file handling. We evaluate whether this added storage-abstraction layer
preserves the sensitivity and specificity reported for file-upload-based
optimized prompting on a public benchmark.

## 2. Methods

### 2.1 Pipeline Architecture

[Summarize the adapter-pattern design from `docs/architecture.md`: the
`StorageAdapter` interface, the Google Drive implementation evaluated in
this study, and the intended extensibility to other backends. Include
the architecture diagram as Figure 1.]

### 2.2 Benchmark Dataset

[Describe BenchSR (Cao et al., 2025) if used as the evaluation dataset:
10 SRs, N citations, provenance. Cite the original paper and its data
availability statement (github.com/JZSang/srma) rather than
reproducing its tables.]

### 2.3 Prompt Design

[Describe your own prompt templates (`prompts/templates.py`) and the
structural patterns they implement — verbatim numbered criteria,
step-by-step reasoning per criterion, instruction repetition for
long documents — with citation to the prior findings each choice is
based on. Do not reproduce any prior paper's example prompt text;
describe your independently authored templates.]

### 2.4 Evaluation Design

[Describe the three-arm comparison: zero-shot, file-upload optimized
prompting (reproduction), and cloud-native pipeline. State model(s)
used, sampling, and statistical methods for sensitivity/specificity
CIs (e.g., Clopper-Pearson, as in Cao et al., 2025, if consistent
comparison is desired).]

### 2.5 Time and Cost Analysis

[Describe how wall-clock time and API cost per review were measured,
and the human-reviewer time/cost estimates used for comparison —
cite literature estimates rather than assuming your own.]

### 2.6 Data Analysis

[Statistical methods, software versions.]

## 3. Results

[To be completed once evaluation is run. Suggested subsections mirroring
Cao et al.: pipeline-vs-file-upload equivalence; performance across
reviews; cost/time savings; failure mode analysis (e.g., scanned PDFs,
Drive API errors).]

## 4. Discussion

[To be completed. Points to address: whether the storage-abstraction
layer changed performance relative to file-upload baselines; practical
implications for review teams already using cloud storage; comparison
with the broader LLM-SR-automation literature.]

## 5. Limitations

- Full-text coverage is bounded by what a review team places in the
  watched folder; the pipeline does not solve full-text retrieval
  itself.
- [Single cloud backend (Google Drive) evaluated despite an
  adapter-based design intended to generalize to other backends —
  state this plainly rather than implying multi-cloud validation.]
- [Convenience sample of benchmark reviews; generalizability to other
  domains/review types.]
- [Scanned-PDF / OCR handling not evaluated in this study.]

## 6. Conclusion

[To be completed.]

## References

[Use a consistent reference manager export. Seed references:]

1. Cao C, Sang J, Arora RK, et al. Development of Prompt Templates for
   Large Language Model–Driven Screening in Systematic Reviews. Ann
   Intern Med. 2025;178:389-401. doi:10.7326/ANNALS-24-02189
2. [ASReview LAB v2 citation]
3. [AiReview / SIGIR 2025 citation]
4. [Rayyan, Abstrackr, RobotAnalyst comparative evaluation — Gates et al.
   2019 / Matyas et al. 2019, as cited in Cao et al.]
5. [Cumpston et al. 2019 Cochrane Handbook]
6. [Add your own prior SR methods papers as relevant]
