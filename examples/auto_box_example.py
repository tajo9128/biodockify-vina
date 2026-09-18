"""
BioDockify Vina - Automatic Bounding Box Calculation Example
Website: https://www.biodockify.com
"""

import os
from biodockify_vina import DockingConfig, VinaDocking

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    receptor = os.path.join(data_dir, "sample_receptor.pdbqt")
    ligand = os.path.join(data_dir, "sample_ligand.pdbqt")

    print("=" * 65)
    print(" BioDockify Vina - Automatic Search Box Detection")
    print(" Platform: https://www.biodockify.com")
    print("=" * 65)

    # Compute bounding box directly from receptor structure coordinates
    config = DockingConfig.auto_box_from_structure(
        filepath=receptor,
        margin=6.0,
        min_size=16.0,
        max_size=28.0,
        exhaustiveness=8,
        num_modes=9,
    )

    print(f"[+] Computed Grid Center (Centroid): {config.center}")
    print(f"[+] Computed Grid Box Size:          {config.size}")
    print(f"[+] Exhaustiveness:                 {config.exhaustiveness}")
    print(f"[+] Max Modes:                      {config.num_modes}")

    # Generate Vina config file syntax
    config_text = config.generate_config_text(
        receptor_path=receptor,
        ligand_path=ligand,
        out_path="output.pdbqt"
    )
    print("\n[+] Generated Vina Config File:")
    print("-" * 40)
    print(config_text.strip())
    print("-" * 40)

if __name__ == "__main__":
    main()
