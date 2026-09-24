#!/usr/bin/env python3
"""
generate_terrain_textures.py — Procedural generator for high-resolution seamless PBR terrain textures.
Synthesizes Indian outdoor off-road textures:
1. laterite_trail.png: Reddish-brown laterite soil with vehicle tracks and gravel.
2. arid_grass.png: Semi-arid scrub grass, straw, and weathered earth.
3. weathered_rock.png: Granite/basalt stone surface with fissures.
4. tree_bark.png: Rough fibrous bark texture.
"""

import os
import numpy as np
import cv2

def make_seamless(img):
    """Apply a smooth boundary blend to ensure seamless 2D tiling."""
    h, w = img.shape[:2]
    overlap = int(min(h, w) * 0.15)
    blended = img.copy()
    
    # Horizontal seam blend
    for x in range(overlap):
        alpha = x / float(overlap)
        blended[:, x] = cv2.addWeighted(img[:, x], alpha, img[:, w - overlap + x], 1.0 - alpha, 0)
        blended[:, w - overlap + x] = blended[:, x]
        
    # Vertical seam blend
    for y in range(overlap):
        alpha = y / float(overlap)
        blended[y, :] = cv2.addWeighted(blended[y, :], alpha, blended[h - overlap + y, :], 1.0 - alpha, 0)
        blended[h - overlap + y, :] = blended[y, :]
        
    return blended

def generate_laterite_trail(size=1024):
    """Indian Deccan/Rajasthan red laterite packed trail texture."""
    base_color = np.array([38, 65, 168], dtype=np.float32) # BGR: deep red-brown laterite
    noise = np.random.normal(0, 18, (size, size, 3)).astype(np.float32)
    img = np.clip(base_color + noise, 0, 255).astype(np.uint8)
    
    # Layered Perlin-like low frequency terrain variation
    low_freq = cv2.resize(np.random.normal(0, 25, (size // 16, size // 16)), (size, size))
    low_freq = cv2.GaussianBlur(low_freq, (65, 65), 0)
    for c in range(3):
        img[:, :, c] = np.clip(img[:, :, c] + low_freq * (0.8 if c == 2 else 0.5), 0, 255)
        
    # Fine gravel specks
    gravel_mask = np.random.rand(size, size) > 0.985
    img[gravel_mask] = np.clip(img[gravel_mask] * 1.35 + 30, 0, 255)
    dark_speck = np.random.rand(size, size) > 0.985
    img[dark_speck] = np.clip(img[dark_speck] * 0.6, 0, 255)
    
    # Slight wheel rut depressions (subtle vertical track bands)
    rut_mask = np.sin(np.linspace(0, 4 * np.pi, size)) ** 4
    for c in range(3):
        img[:, :, c] = np.clip(img[:, :, c] - 15 * rut_mask[np.newaxis, :], 0, 255)
        
    return make_seamless(img)

def generate_arid_grass(size=1024):
    """Semi-arid Deccan scrub grass with dry patchy vegetation and earth."""
    base_soil = np.array([55, 95, 140], dtype=np.float32) # BGR: dry brown soil
    grass_color = np.array([45, 125, 95], dtype=np.float32) # BGR: olive/khaki wild scrub
    
    # Patchiness mask
    patch_noise = cv2.resize(np.random.rand(size // 32, size // 32).astype(np.float32), (size, size))
    patch_noise = cv2.GaussianBlur(patch_noise, (101, 101), 0)
    patch_mask = np.clip((patch_noise - 0.45) * 3.5, 0.0, 1.0)[:, :, np.newaxis]
    
    soil_layer = np.clip(base_soil + np.random.normal(0, 15, (size, size, 3)), 0, 255)
    grass_layer = np.clip(grass_color + np.random.normal(0, 20, (size, size, 3)), 0, 255)
    
    blended = (soil_layer * (1.0 - patch_mask) + grass_layer * patch_mask).astype(np.uint8)
    
    # Fine blades/texture
    blade_noise = np.random.normal(0, 12, (size, size, 3)).astype(np.float32)
    blended = np.clip(blended + blade_noise, 0, 255).astype(np.uint8)
    
    return make_seamless(blended)

def generate_weathered_rock(size=1024):
    """Weathered outdoor granite rock with mineral veins and fractures."""
    base_grey = np.array([110, 115, 120], dtype=np.float32) # BGR granite
    noise = np.random.normal(0, 22, (size, size, 3)).astype(np.float32)
    rock = np.clip(base_grey + noise, 0, 255).astype(np.uint8)
    
    # Macro rock strata / fracture lines
    fissures = cv2.resize(np.random.normal(0, 30, (size // 8, size // 8)), (size, size))
    fissures = cv2.GaussianBlur(fissures, (31, 31), 0)
    fissure_lines = np.abs(fissures) < 2.5
    rock[fissure_lines] = np.clip(rock[fissure_lines] * 0.4, 0, 255)
    
    # Mineral quartz specks
    quartz = np.random.rand(size, size) > 0.99
    rock[quartz] = [210, 215, 220]
    
    return make_seamless(rock)

def generate_tree_bark(size=1024):
    """Rough vertical fibrous tree bark."""
    base_bark = np.array([45, 65, 85], dtype=np.float32) # BGR dark bark
    vertical_ridges = np.sin(np.linspace(0, 48 * np.pi, size))[:, np.newaxis]
    vertical_ridges = cv2.GaussianBlur(vertical_ridges, (1, 15), 0)
    
    noise = np.random.normal(0, 15, (size, size, 3)).astype(np.float32)
    bark = np.clip(base_bark + noise + 25 * vertical_ridges[:, :, np.newaxis], 0, 255).astype(np.uint8)
    return make_seamless(bark)

def main():
    out_dir = os.path.join(os.path.dirname(__file__), '../sim/materials/textures')
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Synthesizing high-resolution terrain textures in {out_dir}...")
    
    trail = generate_laterite_trail(1024)
    cv2.imwrite(os.path.join(out_dir, 'laterite_trail.png'), trail)
    print("  [✓] laterite_trail.png (1024x1024 seamless)")
    
    grass = generate_arid_grass(1024)
    cv2.imwrite(os.path.join(out_dir, 'arid_grass.png'), grass)
    print("  [✓] arid_grass.png (1024x1024 seamless)")
    
    rock = generate_weathered_rock(1024)
    cv2.imwrite(os.path.join(out_dir, 'weathered_rock.png'), rock)
    print("  [✓] weathered_rock.png (1024x1024 seamless)")
    
    bark = generate_tree_bark(1024)
    cv2.imwrite(os.path.join(out_dir, 'tree_bark.png'), bark)
    print("  [✓] tree_bark.png (1024x1024 seamless)")
    
    print("\nTexture synthesis complete.")

if __name__ == '__main__':
    main()
