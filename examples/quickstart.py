"""
BioDockify Vina - Quick Start Example
Website: https://www.biodockify.com
"""

import os
from biodockify_vina import VinaDocking, DockingConfig, find_vina_executable

def main():
    # Paths to sample data
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    receptor = os.path.join(data_dir, "sample_receptor.pdbqt")
    ligand = os.path.join(data_dir, "sample_ligand.pdbqt")

    print("=" * 65)
    print(" BioDockify Vina - Molecular Docking Example")
    print(" Platform: https://www.biodockify.com")
    print("=" * 65)

    # Check Vina installation
    try:
        vina_path = find_vina_executable()
        print(f"[+] Found AutoDock Vina binary at: {vina_path}")
    except Exception as e:
        print(f"[!] Note: {e}")
        print("[!] To run live docking, install vina (e.g. `conda install -c conda-forge vina`).")
        return

    # Define search box configuration
    config = DockingConfig(
        center_x=14.5,
        center_y=21.0,
        center_z=12.0,
        size_x=20.0,
        size_y=20.0,
        size_z=20.0,
        exhaustiveness=8,
        num_modes=9,
        seed=42,
    )

    print(f"[+] Grid Center: {config.center}")
    print(f"[+] Grid Dimensions: {config.size}")
    print("[+] Launching AutoDock Vina docking simulation...")

    docking = VinaDocking(
        receptor=receptor,
        ligand=ligand,
        config=config,
    )

    result = docking.run()

    print("\n" + "=" * 65)
    print(f" Docking Completed Successfully in {result.execution_time_seconds:.2f}s")
    print("=" * 65)
    print(f" Best Binding Affinity: {result.best_affinity} kcal/mol")
    print(f" Total Poses Generated: {result.num_poses}")
    print("-" * 65)
    print(f"{'Mode':<6} | {'Affinity (kcal/mol)':<20} | {'RMSD l.b.':<10} | {'RMSD u.b.':<10}")
    print("-" * 65)
    for pose in result.poses:
        print(f"{pose.mode:<6} | {pose.affinity:<20.2f} | {pose.rmsd_lb:<10.3f} | {pose.rmsd_ub:<10.3f}")
    print("=" * 65)

    # Save top pose
    output_best = "best_docked_mode1.pdbqt"
    if result.poses and result.poses[0].pdbqt_content:
        result.save_best_pose(output_best)
        print(f"[+] Saved top-ranked binding mode to: {os.path.abspath(output_best)}")

    # JSON export demonstration
    print("\n[+] JSON Metadata Preview:")
    print(result.to_json(indent=2))


if __name__ == "__main__":
    main()
