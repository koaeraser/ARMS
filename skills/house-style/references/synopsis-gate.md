# Author-reviewed synopsis gate

Before drafting or substantively rewriting a full paper, prepare `paper_synopsis.md`
from the current brief, manuscript plan, contribution dossier and original author
and external benchmarks. A section outline alone does not satisfy this gate.

The synopsis contains:
- The reader's question, intended article type and bounded contribution.
- One short prose paragraph per planned section: what it establishes, the evidence
  or example it uses, and the logical transition to the following section.
- Main-text versus supplementary scope and a provisional length budget.
- The intended takeaway and a plain-language abstract sketch. Lead the abstract
  with the practical problem; introduce technical distinctions only as needed.
- Source gaps and specific questions requiring author feedback.

A writer or critic first reviews coherence, brief fidelity, unsupported novelty,
abstract accessibility, scope and resemblance to the selected author exemplars.
Record that feedback in `synopsis_review.md` and revise the synopsis. This review
is advisory and cannot supply author approval.

Then STOP before full drafting. Set project state to `AWAITING_SYNOPSIS_APPROVAL`
and present the synopsis to the human author. `synopsis_approval.md` records
PENDING, CHANGES_REQUESTED or APPROVED, the synopsis content hash/version, and the
actual author decision and its source. Never fabricate approval or infer it from
a request to run ARMS, elapsed time, a prior manuscript approval, or an agent's
review. Explicit author approval in the current conversation may be recorded;
the author need not edit a file manually.

On every resume and before dispatching full drafting, verify that approval covers
the current synopsis. Missing, pending, changed or mismatched approval returns to
the gate. Author feedback is incorporated into the synopsis before approval is
requested again. Material changes to the central claim, narrative, scope or brief
invalidate approval; copyediting that preserves the approved substance does not.
An explicit user instruction to bypass the gate takes precedence and must be
recorded as a user override, not fabricated author review.

While pending, source checks and numerical verification may continue; full-paper
prose, section drafting and manuscript assembly may not. The synopsis and abstract
sketch themselves are allowed. Existing manuscript versions remain intact. A
completed historical run is not retrospectively blocked, but a new substantive
revision needs a synopsis for its new brief. Report the pause as author review
pending, never as a failed scientific validation or a completed manuscript.
