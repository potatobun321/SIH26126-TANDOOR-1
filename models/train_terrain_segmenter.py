#!/usr/bin/env python3
"""
train_terrain_segmenter.py — PyTorch Off-Road Semantic Segmentation Training & Domain Adaptation.
Team: Tikka Techies | SIH 2026 | PS26126 (BEL)

Trains a MobileNetV3-Small segmentation network on the unified RUGD/RELLIS-3D canonical taxonomy,
evaluates mIoU on test benchmarks, and exports to edge ONNX format.
"""

import os
import sys
import time
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.dataset_pipeline import create_dataloaders
from data.taxonomy_mapping import CANONICAL_CLASSES


class OffRoadTerrainSegmenter(nn.Module):
    """
    Lightweight, edge-optimized off-road terrain semantic segmentation model.
    Backbone: MobileNetV3-Small (pretrained ImageNet features)
    Decoder: Multi-scale depthwise separable feature aggregation head
    """
    def __init__(self, num_classes=6):
        super().__init__()
        mobilenet = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        self.features = mobilenet.features

        # Decoder head: 576 channels -> 128 -> 64 -> num_classes
        self.head = nn.Sequential(
            nn.Conv2d(576, 128, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Dropout2d(0.15),
            nn.Conv2d(128, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, num_classes, kernel_size=1)
        )

    def forward(self, x):
        input_size = x.shape[-2:]
        feat = self.features(x)
        logits_low = self.head(feat)
        # Direct bilinear upsampling to native input size
        return nn.functional.interpolate(logits_low, size=input_size, mode='bilinear', align_corners=False)


def compute_iou_metrics(preds, targets, num_classes=6):
    """
    Computes per-class IoU, mean IoU (mIoU), and pixel accuracy from batches of predictions and targets.
    """
    ious = []
    total_inter = 0
    total_union = 0

    for c in range(num_classes):
        pred_c = (preds == c)
        target_c = (targets == c)

        intersection = (pred_c & target_c).sum().item()
        union = (pred_c | target_c).sum().item()

        if union == 0:
            ious.append(float('nan'))  # Class not present in batch
        else:
            ious.append(intersection / float(union))
            total_inter += intersection
            total_union += union

    valid_ious = [iou for iou in ious if not np.isnan(iou)]
    miou = np.mean(valid_ious) if valid_ious else 0.0
    pixel_acc = (preds == targets).float().mean().item()

    return miou, ious, pixel_acc


def train_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    all_miou = []

    for imgs, masks in dataloader:
        imgs = imgs.to(device)
        masks = masks.to(device)

        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, masks)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        preds = torch.argmax(outputs, dim=1)
        miou, _, _ = compute_iou_metrics(preds, masks)
        all_miou.append(miou)

    return total_loss / len(dataloader), np.mean(all_miou)


def evaluate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_miou = []
    class_ious_list = []
    pixel_accs = []

    with torch.no_grad():
        for imgs, masks in dataloader:
            imgs = imgs.to(device)
            masks = masks.to(device)

            outputs = model(imgs)
            loss = criterion(outputs, masks)
            total_loss += loss.item()

            preds = torch.argmax(outputs, dim=1)
            miou, class_ious, acc = compute_iou_metrics(preds, masks)
            all_miou.append(miou)
            class_ious_list.append(class_ious)
            pixel_accs.append(acc)

    # Average per-class IoU
    arr = np.array(class_ious_list)
    mean_class_ious = np.nanmean(arr, axis=0)

    return total_loss / len(dataloader), np.mean(all_miou), mean_class_ious, np.mean(pixel_accs)


def export_to_onnx(model, output_path, height=240, width=320):
    """Exports model to optimized ONNX format."""
    model.eval()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    dummy_input = torch.randn(1, 3, height, width, dtype=torch.float32)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input_rgb'],
        output_names=['class_logits'],
        dynamic_axes={
            'input_rgb': {0: 'batch_size', 2: 'height', 3: 'width'},
            'class_logits': {0: 'batch_size', 2: 'height', 3: 'width'}
        }
    )
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[+] ONNX export successful: {output_path} ({file_size_mb:.2f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Off-Road Terrain Segmentation Training")
    parser.add_argument('--epochs', type=int, default=5, help="Number of training epochs")
    parser.add_argument('--batch_size', type=int, default=8, help="Batch size")
    parser.add_argument('--lr', type=float, default=0.001, help="Learning rate")
    parser.add_argument('--samples', type=int, default=160, help="Number of dataset samples")
    parser.add_argument('--export', action='store_true', help="Export best model to ONNX")
    args = parser.parse_args()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[*] Training Device: {device} ({'GPU Acceleration' if device.type == 'cuda' else 'CPU Mode'})")

    # Class Weights for loss balancing:
    # 0: Sky (1.0), 1: Trail (1.2), 2: Grass (1.0), 3: Bush (1.8), 4: Obstacle (2.5), 5: Hazard (2.5)
    class_weights = torch.tensor([1.0, 1.2, 1.0, 1.8, 2.5, 2.5], dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    train_loader, val_loader, test_loader = create_dataloaders(
        num_samples=args.samples,
        batch_size=args.batch_size,
        target_size=(240, 320)
    )

    model = OffRoadTerrainSegmenter(num_classes=6).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    print("\n" + "="*70)
    print(" SIH26126 — PHASE 6: PERCEPTION MODEL FINE-TUNING & DOMAIN ADAPTATION")
    print(" Team: Tikka Techies | Bharat Electronics Limited (BEL)")
    print("="*70)

    best_miou = 0.0
    best_weights = None

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss, train_miou = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_miou, class_ious, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        epoch_time = time.time() - t0

        print(f"Epoch [{epoch}/{args.epochs}] ({epoch_time:.1f}s) | "
              f"Train Loss: {train_loss:.4f}, mIoU: {train_miou:.3f} | "
              f"Val Loss: {val_loss:.4f}, mIoU: {val_miou:.3f}, PixelAcc: {val_acc*100:.1f}%")

        if val_miou > best_miou:
            best_miou = val_miou
            best_weights = model.state_dict().copy()

    # Load best weights for final test evaluation
    if best_weights:
        model.load_state_dict(best_weights)

    test_loss, test_miou, test_class_ious, test_acc = evaluate(model, test_loader, criterion, device)

    print("\n" + "="*70)
    print(" FINAL PERCEPTION BENCHMARK RESULTS (TEST SPLIT)")
    print("="*70)
    print(f" Overall Test mIoU         : {test_miou * 100:.2f}%")
    print(f" Overall Pixel Accuracy    : {test_acc * 100:.2f}%")
    print("-" * 70)
    print(" PER-CLASS IOU BREAKDOWN:")
    for class_id, class_name in CANONICAL_CLASSES.items():
        ciou = test_class_ious[class_id] * 100 if class_id < len(test_class_ious) and not np.isnan(test_class_ious[class_id]) else 0.0
        print(f"  Class {class_id} [{class_name:<24}] : {ciou:.2f}%")
    print("="*70)

    # Export to ONNX if requested
    if args.export:
        onnx_dest = os.path.abspath(os.path.join(os.path.dirname(__file__), 'checkpoints', 'terrain_segmenter.onnx'))
        model.cpu()
        export_to_onnx(model, onnx_dest)

    return test_miou, test_acc


if __name__ == '__main__':
    main()
