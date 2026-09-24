# SIH 2026 Presentation Analysis

## Source status
The primary official source is `sih.gov.in/sih2026PS`, which blocked automated fetch in this research session (bot protection). The facts below are therefore sourced from **secondary aggregators** that themselves claim to summarize the official rules (BlinkNBuild catalogue; independent "how to win SIH" guides). They are internally consistent with each other and with general SIH practice in prior years, which raises confidence, but **none of it should be treated as verified until a team member manually confirms it against the live `sih.gov.in` portal or the official SPOC-distributed guidelines PDF.**

## OFFICIALLY STATED (per secondary sources, unverified against primary) constraints
- Team size: **exactly 6 students**, same institution.
- Gender diversity: **minimum 1 female member** mandatory per team.
- Every team must clear an **internal college-level (SPOC) screening hackathon** before national submission.
- Idea submission format: **PDF only**, built from the **official AICTE PPT template**, **maximum 6 slides**.
- Submission deadline: **30 September 2026**, via `sih.gov.in`.
- Cash prize: **₹1,00,000 per winning problem statement**, plus national mentorship (per secondary source).

**ACTION ITEM:** Have your SPOC download the actual AICTE 6-slide template PDF/PPTX from the official portal and drop it into the repo (e.g., `/docs/official_template.pptx`) so every future contributor — human or AI — works from the real file rather than this description.

## What is NOT confirmed
- No officially published, itemized **judging rubric** (e.g., "30% technical feasibility, 20% innovation...") was located. Any rubric-style breakdown you see online is almost certainly a third party's reconstruction, not an official weighting — do not present it to your team as fact.
- No PS-specific (SIH26126-specific) additional presentation requirements were found beyond the general 6-slide idea template.
- Word/character limits per slide are not confirmed beyond the 6-slide cap itself.

## Comparison: template constraint vs. observed winning-team behavior
Per `SIH_WINNER_PATTERN_ANALYSIS.md`, strong teams appear to compress the same seven conceptual sections (problem, solution, architecture, innovation, feasibility, impact, team) into the 6-slide budget by **merging, not omitting** — e.g., combining "innovation" and "technical architecture" onto one slide with a diagram plus 2–3 callout bullets, rather than a wall of text. The pattern we observed repeatedly (again, from secondary guides, not official material) is:

| Slide (typical, 6-slide budget) | Common content merge |
|---|---|
| 1 | Title, team, PS ID, one-line problem statement |
| 2 | Problem framing (quantified pain point) + who is affected |
| 3 | Proposed solution overview + one architecture diagram |
| 4 | Technical stack + innovation/USP callouts |
| 5 | Feasibility, cost, and implementation/deployment plan |
| 6 | Impact, scalability, and (if room) references/research basis |

This is a **pattern reconstruction**, not a mandated layout — treat it as a starting draft to adapt, not a template to fill blindly.

## Where strong previous teams appear to go beyond the template
Even within a fixed slide count, patterns observed across public winner material (see Deliverable 2) suggest strong teams differentiate through **density of evidence per slide**, not extra slides:
- A single diagram that visually encodes the data flow (rather than a text bullet list) on the architecture slide.
- At least one number that isn't a generic industry statistic — ideally derived from the team's own early testing or simulation, however small-scale.
- An explicit "why not existing solution X" comparison, even if brief — this appears to correlate with the "innovation" framing across the guides reviewed.

## Recommendation for Tikka Techies
1. Do not begin deck design until the actual official template file is in the repo.
2. Treat the 6-slide constraint as a forcing function for the AGENTS.md's own "definition of done" for presentation work — draft content should be written first as a longer research brief (these deliverables), then compressed, not compressed-first.
3. Re-run this research task once the physical/finale-stage template (if different from the idea-stage template) is published, since SIH historically uses a different, less constrained format for the 36-hour build stage.
