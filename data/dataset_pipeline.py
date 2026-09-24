#!/usr/bin/env python3
"""
dataset_pipeline.py — PyTorch Off-Road Terrain Dataset Loader with Indian Domain Adaptation.
Team: Tikka Techies | SIH 2026 | PS26126 (BEL)

Loads off-road terrain images with semantic masks and applies domain transfer augmentations:
- Red/laterite soil color shifts (Indian terrain domain adaptation)
- High-intensity solar glare and shadow contrast (Rajasthan/Jaipur solar irradiance)
- Dust haze simulation and blur
"""

import os
import random
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset, DataLoader
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.taxonomy_mapping import remap_rugd, remap_rellis, CANONICAL_CLASSES


class IndianTerrainDomainAugmentation:
    """
    Domain adaptation augmentations simulating Indian outdoor off-road conditions:
    1. Laterite/Red Soil Shift: Simulates the high-iron red soil common in Indian terrains.
    2. Solar Glare & Harsh Contrast: Simulates intense noon sunlight in semi-arid regions.
    3. Dust/Haze Attenuation: Reduces distant contrast to model airborne particulate matter.
    """
    def __init__(self, p_laterite=0.6, p_glare=0.5, p_dust=0.4):
        self.p_laterite = p_laterite
        self.p_glare = p_glare
        self.p_dust = p_dust

    def __call__(self, img_rgb: np.ndarray) -> np.ndarray:
        out = img_rgb.astype(np.float32)

        # 1. Laterite / Red Soil Hue Shift
        if random.random() < self.p_laterite:
            # Boost red channel slightly and shift green toward warmer ochre
            red_gain = random.uniform(1.08, 1.25)
            blue_attenuation = random.uniform(0.75, 0.92)
            out[:, :, 0] = np.clip(out[:, :, 0] * red_gain, 0, 255)
            out[:, :, 2] = np.clip(out[:, :, 2] * blue_attenuation, 0, 255)

        # 2. Solar Glare / High Specular Contrast
        if random.random() < self.p_glare:
            gamma = random.uniform(0.75, 1.35)
            inv_gamma = 1.0 / gamma
            out = np.clip(((out / 255.0) ** inv_gamma) * 255.0, 0, 255)

        # 3. Dust / Particulate Haze
        if random.random() < self.p_dust:
            haze_intensity = random.uniform(0.10, 0.25)
            dust_color = np.array([190, 175, 150], dtype=np.float32)  # Tan dust hue
            out = out * (1.0 - haze_intensity) + dust_color * haze_intensity
            out = np.clip(out, 0, 255)

        return out.astype(np.uint8)


class OffRoadTerrainDataset(Dataset):
    """
    Off-road terrain segmentation dataset supporting canonical 6-class taxonomy.
    """
    def __init__(self, samples, target_size=(240, 320), is_train=True, apply_domain_adaptation=True):
        self.samples = samples
        self.target_size = target_size  # (H, W)
        self.is_train = is_train
        self.domain_aug = IndianTerrainDomainAugmentation() if (is_train and apply_domain_adaptation) else None

        # Standard ImageNet normalization
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        img_rgb = sample['image']  # (H, W, 3) uint8 RGB
        mask = sample['mask']      # (H, W) uint8 canonical class IDs (0-5)

        # Resize to network input resolution
        img_resized = cv2.resize(img_rgb, (self.target_size[1], self.target_size[0]), interpolation=cv2.INTER_LINEAR)
        mask_resized = cv2.resize(mask, (self.target_size[1], self.target_size[0]), interpolation=cv2.INTER_NEAREST)

        # Spatial augmentations during training
        if self.is_train:
            # Random horizontal flip
            if random.random() > 0.5:
                img_resized = np.fliplr(img_resized)
                mask_resized = np.fliplr(mask_resized)

            # Indian domain adaptation photometric shifts
            if self.domain_aug is not None:
                img_resized = self.domain_aug(img_resized)

        # Normalize and convert to PyTorch tensors
        norm_img = (img_resized.astype(np.float32) / 255.0 - self.mean) / self.std
        tensor_img = torch.from_numpy(np.transpose(norm_img, (2, 0, 1)).copy()).float()
        tensor_mask = torch.from_numpy(mask_resized.copy()).long()

        return tensor_img, tensor_mask


def generate_synthetic_offroad_corpus(num_samples=160, height=240, width=320):
    """
    Generates a diverse synthetic off-road dataset across varied terrain geometry,
    lighting conditions, and obstacle configurations for training & verification.
    """
    samples = []
    for i in range(num_samples):
        # Create base canvas
        img = np.zeros((height, width, 3), dtype=np.uint8)
        mask = np.zeros((height, width), dtype=np.uint8)

        # Sky region (top 25% - 40%)
        horizon = int(height * random.uniform(0.28, 0.42))
        sky_blue = [random.randint(180, 220), random.randint(200, 230), random.randint(235, 255)]
        img[:horizon, :] = sky_blue
        mask[:horizon, :] = 0  # Sky class

        # Ground region
        # Dirt trail winding from bottom toward horizon
        ground_img = np.zeros((height - horizon, width, 3), dtype=np.uint8)
        ground_mask = np.full((height - horizon, width), 2, dtype=np.uint8)  # default grass

        # Base grass texture (green variation)
        g_val = random.randint(110, 160)
        ground_img[:, :] = [random.randint(30, 60), g_val, random.randint(30, 70)]

        # Carve dirt trail (class 1)
        trail_center_start = width // 2 + random.randint(-40, 40)
        trail_center_end = width // 2 + random.randint(-80, 80)
        trail_w_bottom = random.randint(90, 140)
        trail_w_top = random.randint(25, 45)

        gh = height - horizon
        for y in range(gh):
            t = y / float(gh)
            cx = int(trail_center_end * (1 - t) + trail_center_start * t)
            half_w = int(trail_w_top * (1 - t) + trail_w_bottom * t) // 2
            left = max(0, cx - half_w)
            right = min(width, cx + half_w)
            ground_mask[y, left:right] = 1
            # Dirt color (brown/earth)
            dirt_color = [random.randint(130, 170), random.randint(90, 130), random.randint(50, 85)]
            ground_img[y, left:right] = dirt_color

        # Add obstacles: rocks / boulders (class 4)
        num_rocks = random.randint(1, 4)
        for _ in range(num_rocks):
            rx = random.randint(40, width - 40)
            ry = random.randint(int(gh * 0.2), int(gh * 0.85))
            rad = random.randint(8, 22)
            cv2.circle(ground_mask, (rx, ry), rad, 4, -1)
            cv2.circle(ground_img, (rx, ry), rad, (random.randint(60, 90), random.randint(60, 90), random.randint(65, 95)), -1)

        # Add bushes / shrubs (class 3)
        num_bushes = random.randint(2, 6)
        for _ in range(num_bushes):
            bx = random.randint(20, width - 20)
            by = random.randint(int(gh * 0.1), int(gh * 0.9))
            rad = random.randint(10, 25)
            # Only put bush on grass, not directly in middle of trail
            if ground_mask[by, bx] == 2:
                cv2.circle(ground_mask, (bx, by), rad, 3, -1)
                cv2.circle(ground_img, (bx, by), rad, (random.randint(20, 50), random.randint(160, 210), random.randint(30, 60)), -1)

        # Combine
        img[horizon:, :] = ground_img
        mask[horizon:, :] = ground_mask

        samples.append({
            'image': img,
            'mask': mask,
            'id': f"sample_{i:04d}"
        })

    return samples


def create_dataloaders(num_samples=200, batch_size=8, target_size=(240, 320)):
    """Creates train, val, and test PyTorch DataLoaders."""
    samples = generate_synthetic_offroad_corpus(num_samples=num_samples, height=target_size[0], width=target_size[1])
    random.seed(42)
    random.shuffle(samples)

    n_train = int(len(samples) * 0.70)
    n_val = int(len(samples) * 0.15)

    train_samples = samples[:n_train]
    val_samples = samples[n_train:n_train + n_val]
    test_samples = samples[n_train + n_val:]

    train_ds = OffRoadTerrainDataset(train_samples, target_size=target_size, is_train=True, apply_domain_adaptation=True)
    val_ds = OffRoadTerrainDataset(val_samples, target_size=target_size, is_train=False, apply_domain_adaptation=False)
    test_ds = OffRoadTerrainDataset(test_samples, target_size=target_size, is_train=False, apply_domain_adaptation=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    print(f"[+] Dataset Partition: {len(train_ds)} Train, {len(val_ds)} Val, {len(test_ds)} Test samples.")
    return train_loader, val_loader, test_loader


if __name__ == '__main__':
    train_l, val_l, test_l = create_dataloaders(num_samples=50, batch_size=4)
    for imgs, masks in train_l:
        print(f"Batch loaded: Images shape {imgs.shape}, Masks shape {masks.shape}")
        print(f"Mask classes present: {torch.unique(masks).tolist()}")
        break
    print("[+] Dataset pipeline verification complete!")
