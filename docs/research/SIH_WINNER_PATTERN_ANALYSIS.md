# SIH Winner Pattern Analysis

## Source status
No official, SIH-published document titled "judging criteria" or "winner analysis" was located. Everything in this file is either (a) drawn from secondary/tertiary write-ups (guides, blogs, past-winner GitHub repos) or (b) Claude's own pattern-reading across those sources. **Nothing here should be quoted to your team as an official SIH rule.** Use the phrasing discipline modeled below when you cite this file elsewhere: "across publicly available material we reviewed, we repeatedly observed X" — not "SIH requires X."

## What IS officially/semi-officially confirmed about evaluation (from secondary write-ups referencing SIH structure)
- SIH runs two tracks (Software, Hardware) and typically two stages: an **idea/PPT submission** stage, then (if shortlisted) a **36-hour build stage** at a physical or grand-finale event.
- Idea-stage submissions are evaluated as a **document/deck**, not a working demo — so for the idea stage, communication quality is doing real work regardless of your actual technical maturity.
- One secondary source (Zbotic, a hardware-kit vendor writing an SIH guide) states judges evaluate on: **novelty of solution, technical complexity, working prototype, scalability, cost-effectiveness, and impact potential.** This is a paraphrase from a third party, not sourced to an official SIH document — treat it as an **OBSERVED PATTERN / plausible summary**, not confirmed criteria.

## Observed patterns across publicly available winning/finalist material

We reviewed public repositories and guides from SIH 2020–2025 winning/finalist teams (see `SOURCE_REGISTER.md` for the specific repos/links). Recurring patterns, stated as observations, not rules:

### PROBLEM FRAMING
Strong decks open with a **concrete, quantified pain point** tied to the sponsoring body's actual operations (a number, a cost, a frequency) rather than a generic statement of the problem category. Weak decks restate the PS title.

### SOLUTION FRAMING
Winning decks name the solution (a short product name/tagline) early and describe it as a **system with named components**, not a vague capability list. The solution is framed as directly closing the gap named in the problem framing — a visible A→B logical chain.

### ARCHITECTURE
Public winner repos and decks we found range from a single high-level block diagram (most common at idea stage) to, in a minority of strong technical teams, a layered diagram showing data flow between named modules (sensor → processing → model → output → user). We did not find evidence that idea-stage decks commonly include implementation-level architecture (class diagrams, API specs) — that appears reserved for the build/finale stage if at all.

### TECHNOLOGY
Stacks are justified by **fit to constraint** (offline capability, low-cost hardware, multilingual support) rather than by novelty of the technology itself. Several PS text excerpts we retrieved directly (SIH26001–26017) explicitly list "Suggested Technologies," which strong teams appear to treat as a floor, not a ceiling — augmenting rather than just repeating the suggested list.

### INNOVATION
Across the repos reviewed, "innovation" in practice usually meant one of: (a) a genuinely novel algorithmic contribution (rare, mostly among robotics/AI-heavy PS), (b) a clever recombination of existing tools for a specific under-served context (common), or (c) a UX/deployment innovation — offline-first, low-bandwidth, vernacular-language support (very common, and repeatedly emphasized in the official PS texts themselves, e.g., "offline sync," "multilingual notifications" appear in nearly every PS we read in full).

### IMPLEMENTATION
At idea stage, implementation evidence is usually **screenshots or mockups**, sometimes a very early prototype video. It is not expected to be a finished system. Teams that show *any* working component (even a partial pipeline) appear to stand out from those showing only mockups, based on the framing used in multiple "how to win" guides we reviewed — this is our own inference from repeated advice-giver emphasis, not a hard data point.

### VALIDATION
This is the weakest area across almost all public material we reviewed: **few publicly available idea-stage decks show quantitative metrics.** Where metrics appear, they are usually accuracy/F1 for an ML component, or a simple before/after cost or time-saving estimate. This is a genuine opportunity: a deck that shows *any* rigorous quantitative validation (even simulation-only) is differentiated by scarcity, not because a rule requires it.

### FEASIBILITY
Strong decks address deployment cost, existing infrastructure reuse, and a phased rollout plan (pilot → district → national, or similar). This mirrors the "Expected Solution" language in the official PS texts we read directly, which frequently ask for "scalable" and "cost-effective" solutions.

### IMPACT
Nearly universal pattern: a slide translating technical capability into a **social/economic outcome statement** (lives saved, hours saved, ₹ saved, families helped) — directly echoing the language of the official PS texts (e.g., "reduce loss of life," "reduce production losses," "improve income opportunities" all appear verbatim-style in the official texts we fetched).

### DEMONSTRATION
For robotics/hardware-adjacent problem statements specifically, the demonstrations we found most convincing in public videos combined: a live or recorded run, an overlay/dashboard showing the system's internal reasoning (not just the outcome), and a narrated explanation of what would happen if something failed. This is our own synthesis across a small number of examples — treat as a hypothesis to test against more examples once your team has bandwidth, not a proven pattern.

### PRESENTATION DESIGN
Recurring structural pattern across "how to win" guides (multiple independent authors converge on this): **Problem → Solution overview → Technical architecture → Innovation/USP → Feasibility & cost → Impact → Team.** This maps closely to the AICTE idea-template's implied slide budget (6 slides) — meaning most of these sections must be compressed onto shared slides, not each given its own.

### JUDGE COMMUNICATION
The single most repeated piece of advice across independent SIH-winner guides we found: **judges skim.** Numbers, diagrams, and bold headline claims are read; paragraphs are not. Every guide we reviewed independently converges on "less text, more visual" as advice — we treat this convergence itself as the evidence, since no single guide is authoritative.

## Comparative table (illustrative, from public secondary sources — not exhaustive)

| Team / Project (year, if known) | Domain | Notable pattern observed |
|---|---|---|
| Team Vision — "Voco" (SIH 2022, DRDO-recognized per repo README) | Assistive/vocational app | Framed around a named beneficiary group, not a generic user |
| Team Vision — Wool traceability (SIH 2023) | Agriculture/textile | Farm-to-fabric traceability framed as a supply-chain trust problem, with a concrete named workflow |
| KisanSeva (SIH 2020 winner, per repo) | Agriculture | Simple, singular value proposition communicated in the repo README itself |
| Various robotics/YOLO-based fish/object detection entries (SIH 2022–23, per GitHub topic search) | Vision/detection | Use of an off-the-shelf detector (YOLO) as a component, not a novel model — reinforces that integration-over-invention is a common, accepted pattern even among strong entries |

**Caveat:** this table is built from search-result snippets, not full deck reviews. Treat it as a starting point for your own team's deeper review, not a finished analysis.

## Bottom line for Tikka Techies
1. The engineering substance you build should be real (see other deliverables) — but the *idea-stage* deck needs to compress it into a tight problem→solution→architecture→innovation→feasibility→impact structure with heavy visuals and minimal text, per the converging pattern above.
2. Quantitative validation (even in simulation) appears to be a genuine, low-competition differentiator, based on its scarcity in the public material reviewed.
3. Don't over-invest in mockup-only visuals — some visible sign of a working component appears to matter.
