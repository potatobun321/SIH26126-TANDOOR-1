# Research Gaps & Differentiation Opportunities for Tikka Techies

Ranked list. Each entry: evidence the problem exists → existing approaches → weakness/gap → potential TT approach → difficulty → SIH feasibility → demonstration → measurement. All rankings are CURRENT HYPOTHESIS, meant to be revisited once PS26126's real text is confirmed and Phase 0 research deepens.

## Rank 1 — Indian-context outdoor terrain understanding (domain-gap closing)
- **Evidence problem exists:** RELLIS-3D and RUGD (the two most relevant public terrain-segmentation datasets found in this research pass) are both US-captured; no equivalent Indian dataset was identified (see `DATASETS.md`). Domain gap between training and deployment distribution is a well-established general ML failure mode, not a speculative claim.
- **Existing approaches:** transfer learning/fine-tuning from RELLIS-3D/RUGD pretrained models; generic domain adaptation techniques (still an open research area generally, not solved).
- **Gap:** no evidence found of a public, evaluated terrain-segmentation model specifically validated on Indian outdoor/off-road conditions.
- **TT approach:** collect a small, real, locally-captured and hand-labeled Indian outdoor image set (even a few hundred frames from campus/nearby terrain across a couple of lighting/weather conditions); fine-tune a RUGD/RELLIS-3D-pretrained segmentation model on it; **report the measured accuracy delta** before/after fine-tuning as your evidence, not a general claim.
- **Difficulty:** MODERATE (data collection + labeling effort is real but bounded; no novel algorithm required).
- **SIH feasibility:** HIGH — bounded, demonstrable, directly ties to the "outdoor environment" wording in the PS title.
- **Demonstration:** side-by-side segmentation output on the same Indian test scene, pre- vs. post-fine-tuning.
- **Measurement:** mIoU / pixel accuracy on a held-out locally-captured test set.

## Rank 2 — Traversability-aware costmap integration (perception → planning bridge)
- **Evidence problem exists:** Nav2's standard costmap layers are binary/occupancy-based (`EXISTING_SOLUTIONS.md`), which discards the graded traversability information (e.g., "grass is slow but passable, mud is risky, rock is impassable") that a terrain-segmentation model actually produces.
- **Existing approaches:** research papers propose traversability costmaps; not commonly found as a maintained, plug-in-ready Nav2 costmap layer in public repos (unverified — a deeper targeted search for existing "traversability costmap plugin ros2" repos is a recommended Phase 0 task before finalizing this as a gap claim).
- **Gap:** the perception→planning "glue" that turns a segmentation mask into a graded costmap layer.
- **TT approach:** build a custom Nav2 costmap plugin that consumes the terrain-segmentation output and assigns per-class traversal cost, rather than binary drivable/non-drivable.
- **Difficulty:** MODERATE — requires understanding both the perception output format and Nav2's plugin API, but is bounded, well-scoped engineering.
- **SIH feasibility:** HIGH — visually demonstrable (a costmap heatmap is a compelling visualization), technically substantive without requiring new ML research.
- **Demonstration:** Foxglove/RViz visualization of the vehicle preferring a "grass" path over a "mud" path when both are geometrically obstacle-free.
- **Measurement:** path choice correctness against hand-labeled ground-truth preference on test scenes; also collision/near-miss rate versus a binary-costmap baseline.

## Rank 3 — GPS-denied visual localization robustness in low-texture outdoor scenes
- **Evidence problem exists:** documented, repeated limitation of feature-based visual SLAM (ORB-SLAM3, RTAB-Map) in low-texture, repetitive outdoor scenes (`TECHNOLOGY_COMPARISON.md`).
- **Existing approaches:** visual-inertial fusion, direct/semi-direct methods, loop-closure-heavy pipelines.
- **Gap:** most public demonstrations of these techniques are on structured or semi-structured environments, not unstructured off-road outdoor terrain specifically.
- **TT approach:** empirically benchmark 2–3 candidate localization approaches (e.g., RTAB-Map, wheel+IMU fusion, and one visual-inertial method) head-to-head on the *same* simulated (and, if feasible, real) outdoor course, and report drift/failure statistics rather than picking one by reputation.
- **Difficulty:** MODERATE-HIGH — meaningful benchmarking effort, but high research-credibility payoff.
- **SIH feasibility:** MODERATE — valuable but less visually compelling than Rank 1/2 for a judge-facing demo; strong for the "evidence-driven" narrative in the deck.
- **Demonstration:** trajectory-error plot vs. ground truth (simulated) or vs. a surveyed reference path (real).
- **Measurement:** absolute trajectory error (ATE), relative pose error (RPE), tracking-failure count, recovery time — standard SLAM benchmark metrics (see `EVALUATION` conclusions embedded in `AGENTS.md`).

## Rank 4 — Lightweight edge inference for affordable hardware
- **Evidence problem exists:** real-time perception at competition/demo scale usually assumes a capable GPU; affordable embedded platforms (Jetson-class or lower) impose real latency/throughput constraints.
- **Existing approaches:** model quantization, pruning, distillation; smaller backbone architectures.
- **Gap:** most published off-road segmentation baselines report accuracy, not edge-latency, together with Indian-hardware-realistic power/cost budgets.
- **TT approach:** benchmark chosen perception models' actual FPS/latency on the team's real target hardware (not just a desktop GPU), and report the accuracy/speed trade-off explicitly.
- **Difficulty:** LOW-MODERATE (mostly benchmarking + possibly model-size tuning, not new research).
- **SIH feasibility:** HIGH if the team has hardware access; **contingent** on Phase 7 (sim-to-real) actually happening — do not over-commit here if hardware isn't secured.
- **Demonstration:** live FPS counter overlay during demo run.
- **Measurement:** FPS, latency (ms), accuracy at that operating point, power draw if measurable.

## Rank 5 — Dynamic obstacle avoidance in outdoor, GPS-denied conditions
- **Evidence problem exists:** most Nav2 demonstrations assume reasonably reliable localization; dynamic obstacle avoidance while localization is itself uncertain (GPS-denied, vision-only) compounds difficulty.
- **Existing approaches:** Nav2's dynamic obstacle layers + standard local planners (DWB, TEB, etc.) handle moving obstacles reasonably well in indoor/urban contexts.
- **Gap:** limited public evidence of this specifically validated for uncertain-localization off-road scenarios.
- **TT approach:** later-phase stretch goal — inject moving obstacles (simulated pedestrians/vehicles) into the outdoor Gazebo world and measure avoidance success rate under both accurate and degraded localization conditions.
- **Difficulty:** MODERATE-HIGH, and depends on Phases 2–4 landing first.
- **SIH feasibility:** MODERATE — good "advanced/future work" story if time-constrained, full implementation only if ahead of schedule.
- **Demonstration:** simulated moving obstacle avoided in real time with an overlay showing detection→avoidance latency.
- **Measurement:** avoidance success rate, minimum clearance distance, replanning latency.

## Lower-priority / explicitly deprioritized for this project (with reasoning)
- **Explainable navigation decisions** — interesting but hard to make legible in a 36-hour/short-timeline demo without diverting effort from the core pipeline; revisit only if ahead of schedule.
- **Uncertainty-aware navigation (formal probabilistic methods)** — academically rich but high implementation risk for the team's likely skill/time budget; not recommended as a primary differentiator for SIH.
- **Low-cost hardware as the headline differentiator** — plausible but generic; nearly every hardware-adjacent SIH team claims "low-cost" — weak differentiation value per the pattern analysis in Deliverable 2 (novelty via cost claims alone is common, not distinguishing).

## Bottom line
Do **not** manufacture novelty by claiming a new algorithm. The defensible, ranked opportunity for Tikka Techies is: **close the Indian-terrain domain gap (Rank 1) and build the traversability-aware perception→planning bridge (Rank 2)**, both of which are bounded, demonstrable, measurable, and directly respond to the PS's actual wording ("vision-based," "outdoor environment") rather than to a generic robotics wishlist.
