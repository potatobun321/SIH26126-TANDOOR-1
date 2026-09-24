#!/usr/bin/env python3
"""
generate_3d_models.py — Generates textured 3D meshes and Gazebo model packages:
1. realistic_boulder: Faceted weathered granite boulder with UV mapping to weathered_rock.png.
2. scrub_tree: Realistic branching tree trunk + canopy with UV mapping to tree_bark.png and arid_grass.png.
3. rock_cluster: Clustered natural trailside stones.
"""

import os
import math
import numpy as np

def generate_faceted_boulder_obj(obj_path, mtl_path, radius=0.75, height=0.9, rings=8, sectors=12):
    """Generates an irregular faceted boulder mesh with UV coordinates and normals."""
    vertices = []
    uvs = []
    normals = []
    faces = []
    
    np.random.seed(42)  # Deterministic natural roughness
    
    # Bottom pole
    vertices.append((0.0, 0.0, 0.0))
    uvs.append((0.5, 0.0))
    normals.append((0.0, 0.0, -1.0))
    
    # Body rings
    for r in range(1, rings):
        phi = (math.pi * r) / rings
        z = (1.0 - math.cos(phi)) * 0.5 * height
        ring_r = math.sin(phi) * radius
        
        for s in range(sectors):
            theta = (2.0 * math.pi * s) / sectors
            # Perturb vertices for natural rock asymmetry
            noise_r = ring_r * (1.0 + np.random.uniform(-0.18, 0.18))
            noise_z = z + np.random.uniform(-0.06, 0.06)
            
            x = noise_r * math.cos(theta)
            y = noise_r * math.sin(theta)
            vertices.append((x, y, noise_z))
            
            u = s / float(sectors)
            v = r / float(rings)
            uvs.append((u, v))
            
            # Approximate normal
            nx = math.cos(theta) * math.sin(phi)
            ny = math.sin(theta) * math.sin(phi)
            nz = math.cos(phi)
            normals.append((nx, ny, nz))
            
    # Top pole
    vertices.append((0.0, 0.0, height * (1.0 + np.random.uniform(-0.05, 0.05))))
    uvs.append((0.5, 1.0))
    normals.append((0.0, 0.0, 1.0))
    
    # Generate quad/tri faces
    top_idx = len(vertices)
    
    # Bottom cap
    for s in range(sectors):
        next_s = (s + 1) % sectors
        faces.append((1, 2 + s, 2 + next_s))
        
    # Middle rings
    for r in range(rings - 2):
        row1 = 2 + r * sectors
        row2 = row1 + sectors
        for s in range(sectors):
            next_s = (s + 1) % sectors
            v1 = row1 + s
            v2 = row1 + next_s
            v3 = row2 + next_s
            v4 = row2 + s
            faces.append((v1, v2, v3))
            faces.append((v1, v3, v4))
            
    # Top cap
    last_row = 2 + (rings - 2) * sectors
    for s in range(sectors):
        next_s = (s + 1) % sectors
        faces.append((top_idx, last_row + next_s, last_row + s))
        
    # Write OBJ
    with open(obj_path, 'w') as f:
        f.write("# Realistic Boulder Mesh (SIH26126)\n")
        f.write(f"mtllib {os.path.basename(mtl_path)}\n")
        f.write("usemtl BoulderMaterial\n")
        f.write("s 1\n")
        
        for vx, vy, vz in vertices:
            f.write(f"v {vx:.4f} {vy:.4f} {vz:.4f}\n")
        for u, v in uvs:
            f.write(f"vt {u:.4f} {v:.4f}\n")
        for nx, ny, nz in normals:
            f.write(f"vn {nx:.4f} {ny:.4f} {nz:.4f}\n")
            
        for f1, f2, f3 in faces:
            # 1-indexed v/vt/vn
            f.write(f"f {f1}/{f1}/{f1} {f2}/{f2}/{f2} {f3}/{f3}/{f3}\n")

def generate_scrub_tree_obj(obj_path, mtl_path):
    """Generates a dry outdoor scrub tree (tapered trunk + faceted canopy)."""
    vertices = []
    uvs = []
    faces = []
    
    # Trunk: 6-sided cylinder tapering from r=0.35 to r=0.20, height 1.8m
    sectors = 8
    height = 2.0
    r_base = 0.38
    r_top = 0.22
    
    # Trunk vertices (base ring: 0..7, top ring: 8..15)
    for s in range(sectors):
        th = 2.0 * math.pi * s / sectors
        vertices.append((r_base * math.cos(th), r_base * math.sin(th), 0.0))
        uvs.append((s / sectors, 0.0))
    for s in range(sectors):
        th = 2.0 * math.pi * s / sectors
        vertices.append((r_top * math.cos(th), r_top * math.sin(th), height))
        uvs.append((s / sectors, 1.0))
        
    # Canopy: 2-layer low-poly ellipsoid crown from z=1.5m to z=3.8m, radius 1.4m
    canopy_start_idx = len(vertices) + 1
    c_r = 1.3
    c_center_z = 2.7
    
    # Crown bottom, middle, top
    for s in range(sectors):
        th = 2.0 * math.pi * s / sectors
        vertices.append((c_r * 0.7 * math.cos(th), c_r * 0.7 * math.sin(th), c_center_z - 0.7))
        uvs.append((s / sectors, 0.2))
    for s in range(sectors):
        th = 2.0 * math.pi * (s + 0.5) / sectors
        vertices.append((c_r * math.cos(th), c_r * math.sin(th), c_center_z))
        uvs.append((s / sectors, 0.5))
    for s in range(sectors):
        th = 2.0 * math.pi * s / sectors
        vertices.append((c_r * 0.6 * math.cos(th), c_r * 0.6 * math.sin(th), c_center_z + 0.7))
        uvs.append((s / sectors, 0.8))
        
    # Canopy apex
    apex_idx = len(vertices) + 1
    vertices.append((0.0, 0.0, c_center_z + 1.2))
    uvs.append((0.5, 1.0))
    
    with open(obj_path, 'w') as f:
        f.write("# Realistic Scrub Tree Mesh (SIH26126)\n")
        f.write(f"mtllib {os.path.basename(mtl_path)}\n")
        
        for vx, vy, vz in vertices:
            f.write(f"v {vx:.4f} {vy:.4f} {vz:.4f}\n")
        for u, v in uvs:
            f.write(f"vt {u:.4f} {v:.4f}\n")
            
        # Trunk faces (Bark Material)
        f.write("usemtl TrunkMaterial\n")
        for s in range(sectors):
            next_s = (s + 1) % sectors
            v1 = 1 + s
            v2 = 1 + next_s
            v3 = 1 + sectors + next_s
            v4 = 1 + sectors + s
            f.write(f"f {v1}/{v1} {v2}/{v2} {v3}/{v3}\n")
            f.write(f"f {v1}/{v1} {v3}/{v3} {v4}/{v4}\n")
            
        # Canopy faces (Canopy Foliage Material)
        f.write("usemtl FoliageMaterial\n")
        c1 = canopy_start_idx
        c2 = c1 + sectors
        c3 = c2 + sectors
        for s in range(sectors):
            next_s = (s + 1) % sectors
            # lower tier
            f.write(f"f {c1+s}/{c1+s} {c1+next_s}/{c1+next_s} {c2+next_s}/{c2+next_s}\n")
            f.write(f"f {c1+s}/{c1+s} {c2+next_s}/{c2+next_s} {c2+s}/{c2+s}\n")
            # upper tier
            f.write(f"f {c2+s}/{c2+s} {c2+next_s}/{c2+next_s} {c3+next_s}/{c3+next_s}\n")
            f.write(f"f {c2+s}/{c2+s} {c3+next_s}/{c3+next_s} {c3+s}/{c3+s}\n")
            # apex
            f.write(f"f {c3+s}/{c3+s} {c3+next_s}/{c3+next_s} {apex_idx}/{apex_idx}\n")

def main():
    models_dir = os.path.join(os.path.dirname(__file__), '../sim/models')
    
    # 1. Realistic Boulder Model
    boulder_dir = os.path.join(models_dir, 'realistic_boulder')
    os.makedirs(os.path.join(boulder_dir, 'meshes'), exist_ok=True)
    obj_path = os.path.join(boulder_dir, 'meshes', 'boulder.obj')
    mtl_path = os.path.join(boulder_dir, 'meshes', 'boulder.mtl')
    generate_faceted_boulder_obj(obj_path, mtl_path)
    
    with open(mtl_path, 'w') as f:
        f.write("newmtl BoulderMaterial\n")
        f.write("Ka 0.8 0.8 0.8\n")
        f.write("Kd 0.9 0.9 0.9\n")
        f.write("map_Kd ../../../materials/textures/weathered_rock.png\n")
        
    with open(os.path.join(boulder_dir, 'model.sdf'), 'w') as f:
        f.write("""<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="realistic_boulder">
    <static>true</static>
    <link name="link">
      <collision name="col">
        <geometry>
          <cylinder>
            <radius>0.72</radius>
            <length>0.9</length>
          </cylinder>
        </geometry>
      </collision>
      <visual name="vis">
        <geometry>
          <mesh>
            <uri>meshes/boulder.obj</uri>
          </mesh>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>""")
    print("  [✓] Generated sim/models/realistic_boulder")

    # 2. Realistic Scrub Tree Model
    tree_dir = os.path.join(models_dir, 'scrub_tree')
    os.makedirs(os.path.join(tree_dir, 'meshes'), exist_ok=True)
    t_obj = os.path.join(tree_dir, 'meshes', 'tree.obj')
    t_mtl = os.path.join(tree_dir, 'meshes', 'tree.mtl')
    generate_scrub_tree_obj(t_obj, t_mtl)
    
    with open(t_mtl, 'w') as f:
        f.write("newmtl TrunkMaterial\n")
        f.write("Ka 0.7 0.7 0.7\n")
        f.write("Kd 0.8 0.8 0.8\n")
        f.write("map_Kd ../../../materials/textures/tree_bark.png\n\n")
        f.write("newmtl FoliageMaterial\n")
        f.write("Ka 0.6 0.8 0.4\n")
        f.write("Kd 0.5 0.7 0.3\n")
        f.write("map_Kd ../../../materials/textures/arid_grass.png\n")
        
    with open(os.path.join(tree_dir, 'model.sdf'), 'w') as f:
        f.write("""<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="scrub_tree">
    <static>true</static>
    <link name="link">
      <collision name="col">
        <geometry>
          <cylinder>
            <radius>0.42</radius>
            <length>3.2</length>
          </cylinder>
        </geometry>
        <origin xyz="0 0 1.6" rpy="0 0 0"/>
      </collision>
      <visual name="vis">
        <geometry>
          <mesh>
            <uri>meshes/tree.obj</uri>
          </mesh>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>""")
    print("  [✓] Generated sim/models/scrub_tree")
    print("3D Model Generation Complete.")

if __name__ == '__main__':
    main()
