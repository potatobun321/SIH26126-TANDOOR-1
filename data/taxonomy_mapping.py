#!/usr/bin/env python3
"""
taxonomy_mapping.py — Unified Off-Road Semantic Segmentation Taxonomy Mapping.
Team: Tikka Techies | SIH 2026 | PS26126 (BEL)

Maps heterogeneous open-source datasets (RUGD 24-class, RELLIS-3D 20-class)
into the unified 6-class SIH26126 UGV Nav2 Cost Scheme.
"""

import numpy as np

# Canonical SIH26126 UGV Class Scheme
CANONICAL_CLASSES = {
    0: 'Sky/Background',
    1: 'Trail/Dirt/Gravel',
    2: 'Grass/Low-Soil',
    3: 'Bush/Dense-Vegetation',
    4: 'Rock/Tree/Obstacle',
    5: 'Water/Puddle/Mud'
}

CANONICAL_COSTS = {
    0: 0,    # Sky (ignored on ground costmap)
    1: 0,    # Trail: Optimal low-drag drivable path
    2: 30,   # Grass: Drivable with light rolling resistance
    3: 140,  # Bush: High friction / risky vegetation
    4: 254,  # Rock/Tree/Wall: Lethal physical obstacle
    5: 254   # Water/Puddle/Deep-Mud: Non-traversable hazard
}

CANONICAL_COLORS_RGB = {
    0: (135, 206, 235),  # Sky / Horizon (Light Blue)
    1: (180, 110, 50),   # Trail / Path (Earth Brown)
    2: (40, 180, 60),    # Grass / Soil (Vibrant Green)
    3: (220, 200, 30),   # Bush / Shrub (Yellow-Gold)
    4: (230, 40, 40),    # Rock / Tree / Obstacle (Crimson Red)
    5: (30, 100, 240)    # Water / Mud (Deep Blue)
}

# -------------------------------------------------------------------------
# RUGD Dataset (24 Classes) -> Canonical Mapping
# Reference: Wigness et al., "RUGD: A Dataset for Autonomous Navigation in Unstructured Outdoor Environments", IROS 2019
# -------------------------------------------------------------------------
RUGD_TAXONOMY = {
    0: ('void', 0),                  # Unlabeled / background
    1: ('dirt', 1),                  # Drivable trail
    2: ('sand', 1),                  # Drivable trail
    3: ('grass', 2),                 # Grass / light resistance
    4: ('tree', 4),                  # Lethal obstacle
    5: ('pole', 4),                  # Lethal obstacle
    6: ('water', 5),                 # Hazard
    7: ('sky', 0),                   # Sky / background
    8: ('vehicle', 4),               # Moving/static obstacle
    9: ('container/generic-obj', 4), # Obstacle
    10: ('asphalt', 1),              # Smooth road
    11: ('gravel', 1),               # Drivable surface
    12: ('building', 4),             # Lethal obstacle
    13: ('mulch', 2),                # Soft ground
    14: ('rock-bed', 3),             # Uneven ground / rough
    15: ('rock', 4),                 # Lethal boulder / rock
    16: ('log', 4),                  # Fallen log / obstacle
    17: ('fence', 4),                # Barrier / obstacle
    18: ('bush', 3),                 # Dense brush / shrub
    19: ('sign', 4),                 # Obstacle
    20: ('bridge', 1),               # Drivable structure
    21: ('concrete', 1),             # Drivable paved area
    22: ('picnic-table', 4),         # Obstacle
    23: ('barrier', 4)               # Obstacle
}

# -------------------------------------------------------------------------
# RELLIS-3D Dataset (20 Classes) -> Canonical Mapping
# Reference: Jiang et al., "RELLIS-3D Dataset: Data, Analysis and Evaluation for Off-road Autonomous Navigation", ICRA 2021
# -------------------------------------------------------------------------
RELLIS_TAXONOMY = {
    0: ('void', 0),                  # Unlabeled
    1: ('dirt', 1),                  # Trail
    2: ('grass', 2),                 # Grass
    3: ('tree', 4),                  # Obstacle
    4: ('pole', 4),                  # Obstacle
    5: ('water', 5),                 # Hazard
    6: ('sky', 0),                   # Sky
    7: ('vehicle', 4),               # Obstacle
    8: ('object', 4),                # Obstacle
    9: ('asphalt', 1),               # Road
    10: ('building', 4),             # Obstacle
    11: ('log', 4),                  # Obstacle
    12: ('person', 4),               # Personnel / dynamic obstacle
    13: ('fence', 4),                # Obstacle
    14: ('bush', 3),                 # Dense shrub
    15: ('concrete', 1),             # Trail
    16: ('barrier', 4),              # Obstacle
    17: ('puddle', 5),               # Hazard
    18: ('mud', 5),                  # Soft soil hazard
    19: ('rubble', 4)                # Rough rubble / obstacle
}

# Build Fast LUT Lookups
RUGD_LUT = np.array([RUGD_TAXONOMY[i][1] for i in range(24)], dtype=np.uint8)
RELLIS_LUT = np.array([RELLIS_TAXONOMY[i][1] for i in range(20)], dtype=np.uint8)


def remap_rugd(mask: np.ndarray) -> np.ndarray:
    """Remap a 2D/3D integer mask from RUGD raw class IDs to canonical 0-5 IDs."""
    clipped = np.clip(mask, 0, len(RUGD_LUT) - 1)
    return RUGD_LUT[clipped]


def remap_rellis(mask: np.ndarray) -> np.ndarray:
    """Remap a 2D/3D integer mask from RELLIS-3D raw class IDs to canonical 0-5 IDs."""
    clipped = np.clip(mask, 0, len(RELLIS_LUT) - 1)
    return RELLIS_LUT[clipped]


def classes_to_nav2_costs(mask: np.ndarray) -> np.ndarray:
    """Convert canonical class mask (0-5) to 0-254 Nav2 cost values."""
    cost_lut = np.array([CANONICAL_COSTS[i] for i in range(6)], dtype=np.uint8)
    return cost_lut[np.clip(mask, 0, 5)]


if __name__ == '__main__':
    print("=== SIH26126 Taxonomy Mapping Verification ===")
    print(f"Canonical Classes: {CANONICAL_CLASSES}")
    print(f"Canonical Nav2 Costs: {CANONICAL_COSTS}")

    # Test RUGD remapping
    test_rugd = np.array([1, 3, 15, 18, 6, 7], dtype=np.uint8)
    remapped_rugd = remap_rugd(test_rugd)
    print(f"RUGD Raw [dirt, grass, rock, bush, water, sky] -> Canonical: {remapped_rugd.tolist()}")
    assert np.array_equal(remapped_rugd, [1, 2, 4, 3, 5, 0]), "RUGD remapping error!"

    # Test RELLIS remapping
    test_rellis = np.array([1, 2, 3, 14, 18, 6], dtype=np.uint8)
    remapped_rellis = remap_rellis(test_rellis)
    print(f"RELLIS Raw [dirt, grass, tree, bush, mud, sky]   -> Canonical: {remapped_rellis.tolist()}")
    assert np.array_equal(remapped_rellis, [1, 2, 4, 3, 5, 0]), "RELLIS remapping error!"

    # Test Nav2 cost mapping
    costs = classes_to_nav2_costs(remapped_rugd)
    print(f"Nav2 Injected Costs: {costs.tolist()}")
    assert np.array_equal(costs, [0, 30, 254, 140, 254, 0]), "Cost mapping error!"

    print("[+] All Taxonomy verification assertions passed successfully!")
