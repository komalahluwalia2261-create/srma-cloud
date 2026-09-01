"""
Screening prompt templates.

These are original implementations of the structural patterns reported to
help criteria-based LLM screening in the prior literature (see docs/
architecture.md for citations): numbered, verbatim eligibility criteria;
explicit chain-of-thought reasoning tied to each criterion; and, for long
documents, repeating the instructions before *and* after the document body
to counter "lost in the middle" effects. No prompt text is copied from any
source paper — only the structural pattern is reused, and it is reused
because prior work reports it materially improves sensitivity.

`criteria` is inserted verbatim from the review protocol (do not
paraphrase it — prior work found paraphrased/inferred criteria hurt
performance relative to the protocol's original wording).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewCriteria:
    objectives: str
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))


def build_abstract_prompt(criteria: ReviewCriteria, title: str, abstract: str) -> str:
    return f"""You are screening one citation for a systematic review.

REVIEW OBJECTIVES (verbatim from protocol):
{criteria.objectives}

INCLUSION CRITERIA (all must be satisfied):
{_numbered(criteria.inclusion_criteria)}

EXCLUSION CRITERIA (any one is sufficient to exclude):
{_numbered(criteria.exclusion_criteria)}

CITATION:
Title: {title}
Abstract: {abstract}

Work through each inclusion and exclusion criterion in turn and state
briefly whether the abstract satisfies it, is unclear, or fails it.
Abstracts are necessarily incomplete, so where information is missing
prefer including the citation for full-text review rather than excluding
on the basis of absence of evidence.

Conclude with a line containing only DECISION: INCLUDE, DECISION: EXCLUDE,
or DECISION: UNCERTAIN.
"""


def build_full_text_prompt(criteria: ReviewCriteria, full_text: str) -> str:
    criteria_block = f"""REVIEW OBJECTIVES (verbatim from protocol):
{criteria.objectives}

INCLUSION CRITERIA (all must be satisfied):
{_numbered(criteria.inclusion_criteria)}

EXCLUSION CRITERIA (any one is sufficient to exclude):
{_numbered(criteria.exclusion_criteria)}"""

    instructions = """Work through each inclusion and exclusion criterion in turn, citing the
part of the article that supports your judgment for each one. Full texts
are long, so the criteria are repeated below after the article — treat
both copies as identical and use whichever is more convenient to refer
back to while reasoning.

Conclude with a line containing only DECISION: INCLUDE, DECISION: EXCLUDE,
or DECISION: UNCERTAIN."""

    # Instructions + criteria repeated before and after the article body,
    # per the "init + fin" structure noted above.
    return f"""{criteria_block}

{instructions}

ARTICLE FULL TEXT:
{full_text}

{criteria_block}

{instructions}
"""
