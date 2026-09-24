#!/usr/bin/env python3
"""
export_onnx.py — Export a lightweight off-road terrain semantic segmentation model to ONNX.
Produces: models/checkpoints/terrain_segmenter.onnx
"""

import os
import torch
import torch.nn as nn
import torchvision.models as models

class OffRoadTerrainSegmenter(nn.Module):
    """
    Lightweight, real-time semantic segmentation network for outdoor UGV navigation.
    Backbone: MobileNetV3-Small (fast edge feature extractor)
    Head: Lightweight Feature Pyramid / Segmentation Head (6 classes)
    """
    def __init__(self, num_classes=6):
        super().__init__()
        # Load MobileNetV3-Small features
        mobilenet = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        self.features = mobilenet.features

        # Decoder / Segmentation Head
        # MobileNetV3-Small outputs 576 channels at 1/32 scale
        self.head = nn.Sequential(
            nn.Conv2d(576, 128, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, num_classes, kernel_size=1)
        )

    def forward(self, x):
        input_size = x.shape[-2:]
        feat = self.features(x)
        logits_low = self.head(feat)
        # Upsample directly to input resolution
        logits = nn.functional.interpolate(logits_low, size=input_size, mode='bilinear', align_corners=False)
        return logits

def main():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'checkpoints'))
    os.makedirs(output_dir, exist_ok=True)
    onnx_path = os.path.join(output_dir, 'terrain_segmenter.onnx')

    print("Building lightweight Off-Road Terrain Segmentation model...")
    model = OffRoadTerrainSegmenter(num_classes=6)
    model.eval()

    # Input: (Batch=1, Channels=3, Height=240, Width=320)
    dummy_input = torch.randn(1, 3, 240, 320, dtype=torch.float32)

    print(f"Exporting to ONNX format at {onnx_path}...")
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
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

    print(f"Model exported successfully! File size: {os.path.getsize(onnx_path) / (1024 * 1024):.2f} MB")

    # Verify with ONNX Runtime
    import onnxruntime as ort
    session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: dummy_input.numpy()})
    print(f"ONNX Runtime verification passed! Output shape: {outputs[0].shape}")

if __name__ == '__main__':
    main()
