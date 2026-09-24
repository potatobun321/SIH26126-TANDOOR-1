# Datasets

## RELLIS-3D
- **Environment:** off-road terrain at Rellis Campus, Texas A&M (grass, trees, trails, mud).
- **Sensors:** stereo camera, LiDAR (Ouster), GPS/IMU — multimodal.
- **Annotations:** pixel-level semantic segmentation (~20 classes: grass, tree, bush, puddle, mud, rubble, barrier, etc.), plus 3D LiDAR point-level semantic labels.
- **Size:** ~13,556 annotated image frames (per the dataset's published statistics) with corresponding LiDAR scans.
- **License:** research/academic use license — verify current exact terms on the official release page before any commercial-adjacent use; SIH demonstration/research use is very likely fine but should still be checked and cited properly.
- **Tasks supported:** semantic segmentation (image and point cloud), suitable for traversability-class training.
- **Suitability for PS26126:** HIGH for terrain-class model pretraining/fine-tuning; the class taxonomy (grass/mud/puddle/obstacle) maps well onto "outdoor traversability."
- **Limitations:** single geographic site (Texas), specific vegetation/soil types, no Indian terrain, no monsoon/dust conditions, class imbalance (some classes like "puddle" are rare).
- **Train/validate split:** usable for both — has an official train/val/test split.
- **Resemblance to Indian outdoor deployment context:** LOW-MODERATE — vegetation types, soil color/texture, and lighting differ meaningfully from typical Indian outdoor/campus/semi-rural terrain. Treat as a **pretraining base**, not a final-accuracy guarantee; fine-tuning or domain adaptation on locally captured data is very likely necessary for credible claims.

## RUGD (RUGD Off-road Ground Dataset)
- **Environment:** varied off-road trails/environments (creek beds, trails, parks) across multiple US sites.
- **Sensors:** RGB camera only (no LiDAR) — this is a key structural difference from RELLIS-3D.
- **Annotations:** dense pixel-level semantic segmentation (~24 classes).
- **Size:** tens of thousands of labeled frames across multiple video sequences (exact current count should be re-verified against the dataset's official page at use time).
- **License:** research use — verify current terms.
- **Tasks supported:** semantic segmentation (vision-only) — closely matches this PS's "vision-based" constraint better than RELLIS-3D's LiDAR-centric framing.
- **Suitability for PS26126:** HIGH, arguably a better primary fit than RELLIS-3D specifically because it's RGB-only, matching the "vision-based" requirement without implying LiDAR dependence.
- **Limitations:** same geography/vegetation-mismatch concern as RELLIS-3D; class taxonomy differs slightly from RELLIS-3D, so combining both requires a taxonomy-mapping step, not a naive merge.
- **Resemblance to Indian context:** LOW-MODERATE, same caveat as above.

## Other datasets worth investigating (CANDIDATE, not yet deeply reviewed in this pass)
- **Freiburg Forest dataset** — RGB + NIR + depth, forest/off-road, semantic segmentation, smaller scale, European forest vegetation. Useful as an additional pretraining source.
- **CaSSeD / IDD (India Driving Dataset)** — IDD in particular is **directly relevant** as an Indian-context dataset, though it is oriented toward on-road/semi-structured Indian traffic/street scenes rather than off-road terrain; still likely the closest thing to "domain-relevant Indian imagery" publicly available and should be investigated in depth in a follow-up research pass — **this is flagged as a priority gap-filling action, not yet completed here.**
- **KITTI, Oxford RobotCar, and similar SLAM/odometry benchmarks** — useful for benchmarking visual SLAM/odometry accuracy, but urban/on-road, not off-road — relevant to the localization sub-problem's evaluation methodology, not to terrain segmentation.
- **TartanDrive / TartanAir** — off-road driving and synthetic-scene datasets from CMU, worth investigating for sim-to-real and off-road dynamics research; not deeply reviewed here.

## Identified dataset gap (this is the team's clearest, most defensible research gap — see `RESEARCH_GAPS.md`)
**No publicly identified, large-scale, densely-annotated dataset for outdoor/off-road terrain segmentation captured in Indian conditions (vegetation, soil color, monsoon haze, dust, informal trail structure) was found during this research pass.** This is stated as an observation from the specific sources checked in this session, not as an exhaustive literature claim — a dedicated follow-up literature search (including Indian university/DRDO/ISRO-affiliated robotics labs) is a recommended Phase 0 task before relying on this gap as your core differentiation pitch.

## Practical recommendation
1. Use RUGD (vision-only, matches PS constraint) as the primary segmentation pretraining source, RELLIS-3D as a secondary/augmentation source, with an explicit class-taxonomy mapping table maintained in the repo.
2. Budget time in Phase 2/6 (see `ENGINEERING_ROADMAP.md`) to collect even a small, locally captured, hand-labeled Indian outdoor terrain dataset (campus grounds, nearby semi-rural terrain) — this directly supports both the "domain gap" research question and a genuine, demonstrable differentiation claim.
3. Never claim "trained on Indian terrain" unless you have actually collected and used Indian-terrain data — this maps directly to AGENTS.md rule 11 (no unearned claims of robustness/accuracy).
