#!/usr/bin/env python3
"""
evaluate_miou.py — Quantitative Evaluation & Domain Gap Analysis for SIH26126.
Team: Tikka Techies | SIH 2026 | PS26126 (BEL)

Evaluates the trained/fine-tuned model on:
1. Standard Benchmark (Baseline Western Off-Road)
2. Indian Domain Adaptation Benchmark (Laterite soil, high solar glare, dust haze)
Measures the Domain Transfer Delta (Δ mIoU) to substantiate Rank 1 Innovation claims.
"""

import os
import sys
import time
import argparse
import numpy as np
import cv2
import onnxruntime as ort

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.dataset_pipeline import generate_synthetic_offroad_corpus, IndianTerrainDomainAugmentation
from data.taxonomy_mapping import CANONICAL_CLASSES


def run_onnx_inference(session, img_rgb, input_size=(240, 320)):
    h, w = img_rgb.shape[:2]
    resized = cv2.resize(img_rgb, (input_size[1], input_size[0]))

    # Normalize
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    norm = (resized.astype(np.float32) / 255.0 - mean) / std
    tensor = np.transpose(norm, (2, 0, 1))[np.newaxis, ...].astype(np.float32)

    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: tensor})
    logits = outputs[0][0]  # (C, H, W)
    pred_low = np.argmax(logits, axis=0).astype(np.uint8)
    return cv2.resize(pred_low, (w, h), interpolation=cv2.INTER_NEAREST)


def evaluate_dataset(session, samples, apply_indian_domain=False):
    aug = IndianTerrainDomainAugmentation(p_laterite=1.0, p_glare=0.8, p_dust=0.7) if apply_indian_domain else None

    num_classes = len(CANONICAL_CLASSES)
    confusion = np.zeros((num_classes, num_classes), dtype=np.int64)

    t_start = time.perf_counter()
    for sample in samples:
        img = sample['image']
        gt = sample['mask']

        if aug:
            img = aug(img)

        pred = run_onnx_inference(session, img)

        for true_c in range(num_classes):
            for pred_c in range(num_classes):
                confusion[true_c, pred_c] += np.sum((gt == true_c) & (pred == pred_c))

    latency_ms = ((time.perf_counter() - t_start) / len(samples)) * 1000.0

    # Compute per-class IoU from confusion matrix
    ious = []
    precisions = []
    recalls = []

    for c in range(num_classes):
        tp = confusion[c, c]
        fp = np.sum(confusion[:, c]) - tp
        fn = np.sum(confusion[c, :]) - tp

        denom = tp + fp + fn
        iou = tp / float(denom) if denom > 0 else float('nan')
        ious.append(iou)

        prec = tp / float(tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / float(tp + fn) if (tp + fn) > 0 else 0.0
        precisions.append(prec)
        recalls.append(rec)

    valid_ious = [v for v in ious if not np.isnan(v)]
    miou = np.mean(valid_ious) if valid_ious else 0.0
    pixel_acc = np.trace(confusion) / float(np.sum(confusion))

    return {
        'miou': miou,
        'pixel_acc': pixel_acc,
        'class_ious': ious,
        'precisions': precisions,
        'recalls': recalls,
        'latency_ms': latency_ms,
        'fps': 1000.0 / latency_ms if latency_ms > 0 else 0.0
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate mIoU and Indian Domain Adaptation Gap")
    parser.add_argument('--model', type=str, default='models/checkpoints/terrain_segmenter.onnx', help="Path to ONNX model")
    parser.add_argument('--test_samples', type=int, default=50, help="Number of test images")
    args = parser.parse_args()

    if not os.path.exists(args.model):
        print(f"[!] Error: Model file {args.model} not found. Please train first!")
        sys.exit(1)

    print(f"[*] Loading ONNX Model: {args.model}")
    session = ort.InferenceSession(args.model, providers=['CPUExecutionProvider'])

    print(f"[*] Generating {args.test_samples} test scenes across off-road conditions...")
    samples = generate_synthetic_offroad_corpus(num_samples=args.test_samples)

    # 1. Standard Benchmark
    print("[*] Evaluating on Standard Off-Road Benchmark...")
    res_std = evaluate_dataset(session, samples, apply_indian_domain=False)

    # 2. Indian Domain Adaptation Benchmark (Adversarial Laterite, Glare, Haze)
    print("[*] Evaluating on Indian Domain Adaptation Benchmark...")
    res_indian = evaluate_dataset(session, samples, apply_indian_domain=True)

    print("\n" + "="*75)
    print(" SIH26126 — PERCEPTION EVALUATION & DOMAIN ADAPTATION BENCHMARK")
    print(" Team: Tikka Techies | Bharat Electronics Limited (BEL)")
    print("="*75)
    print(f"{'Evaluation Split':<32} | {'mIoU (%)':<10} | {'Pixel Acc (%)':<15} | {'Latency (ms)':<12} | {'FPS':<6}")
    print("-" * 75)
    print(f"{'Standard Off-Road Benchmark':<32} | {res_std['miou']*100:<10.2f} | {res_std['pixel_acc']*100:<15.2f} | {res_std['latency_ms']:<12.2f} | {res_std['fps']:<6.1f}")
    print(f"{'Indian Terrain Domain (Laterite/Glare)':<32} | {res_indian['miou']*100:<10.2f} | {res_indian['pixel_acc']*100:<15.2f} | {res_indian['latency_ms']:<12.2f} | {res_indian['fps']:<6.1f}")
    print("="*75)

    print("\nPER-CLASS IOU BREAKDOWN (Standard vs Indian Domain):")
    print(f"{'Class ID & Name':<28} | {'Standard IoU':<15} | {'Indian Domain IoU':<18} | {'Delta':<8}")
    print("-" * 75)
    for c, name in CANONICAL_CLASSES.items():
        std_iou = res_std['class_ious'][c] * 100 if not np.isnan(res_std['class_ious'][c]) else 0.0
        ind_iou = res_indian['class_ious'][c] * 100 if not np.isnan(res_indian['class_ious'][c]) else 0.0
        delta = ind_iou - std_iou
        print(f"[{c}] {name:<24} | {std_iou:<14.2f}% | {ind_iou:<17.2f}% | {delta:+.2f}%")
    print("="*75)


if __name__ == '__main__':
    main()
