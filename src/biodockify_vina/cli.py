"""
BioDockify Vina Command-Line Interface (CLI).

BioDockify (https://www.biodockify.com)
"""

import argparse
import json
import os
import sys
from typing import List, Optional

from . import __version__
from .config import DockingConfig
from .docking import VinaDocking, find_vina_executable
from .exceptions import BiodockifyVinaError, VinaExecutableNotFoundError


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="biodockify-vina",
        description=(
            "BioDockify Vina: Single-molecule AutoDock Vina molecular docking runner.\n"
            "Developed by BioDockify (https://www.biodockify.com)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"biodockify-vina {__version__} (https://www.biodockify.com)",
    )

    parser.add_argument(
        "--check-vina",
        action="store_true",
        help="Check if AutoDock Vina binary is found on system PATH and print its path.",
    )

    # Input structures
    input_group = parser.add_argument_group("Input Structures")
    input_group.add_argument(
        "--receptor", "-r",
        type=str,
        help="Path to receptor PDBQT file.",
    )
    input_group.add_argument(
        "--ligand", "-l",
        type=str,
        help="Path to ligand PDBQT file.",
    )

    # Search space definition
    grid_group = parser.add_argument_group("Search Grid Box")
    grid_group.add_argument(
        "--auto-box",
        action="store_true",
        help="Automatically compute grid center and bounding box size from receptor structure.",
    )
    grid_group.add_argument(
        "--center",
        nargs=3,
        type=float,
        metavar=("X", "Y", "Z"),
        help="Grid box center coordinates (x y z) in Angstroms.",
    )
    grid_group.add_argument(
        "--size",
        nargs=3,
        type=float,
        default=[20.0, 20.0, 20.0],
        metavar=("X", "Y", "Z"),
        help="Grid box dimensions (size_x size_y size_z) in Angstroms (default: 20 20 20).",
    )
    grid_group.add_argument(
        "--margin",
        type=float,
        default=8.0,
        help="Padding margin in Angstroms when using --auto-box (default: 8.0).",
    )

    # Docking parameters
    params_group = parser.add_argument_group("Docking Parameters")
    params_group.add_argument(
        "--exhaustiveness", "-e",
        type=int,
        default=8,
        help="Search exhaustiveness (default: 8).",
    )
    params_group.add_argument(
        "--num-modes", "-n",
        type=int,
        default=9,
        help="Maximum number of binding modes to generate (default: 9).",
    )
    params_group.add_argument(
        "--energy-range",
        type=float,
        default=3.0,
        help="Maximum energy difference (kcal/mol) between best and worst modes (default: 3.0).",
    )
    params_group.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible docking results (default: 42).",
    )
    params_group.add_argument(
        "--cpu",
        type=int,
        default=None,
        help="Number of CPU cores to utilize (default: auto-detect).",
    )
    params_group.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Maximum execution timeout in seconds (default: 600).",
    )
    params_group.add_argument(
        "--vina-executable",
        type=str,
        default=None,
        help="Path to custom AutoDock Vina binary.",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--out-dir", "-o",
        type=str,
        default=None,
        help="Directory to save docking outputs (default: temporary directory).",
    )
    output_group.add_argument(
        "--save-best",
        type=str,
        default=None,
        help="Filepath to save the top-ranked (mode 1) pose PDBQT.",
    )
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Print structured results in JSON format to stdout.",
    )

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.check_vina:
        try:
            exe = find_vina_executable(parsed_args.vina_executable)
            print(f"AutoDock Vina detected: {exe}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2

    if not parsed_args.receptor or not parsed_args.ligand:
        parser.print_help()
        print("\nError: Both --receptor (-r) and --ligand (-l) are required for docking.", file=sys.stderr)
        return 1

    try:
        # Determine config
        if parsed_args.auto_box:
            config = DockingConfig.auto_box_from_structure(
                filepath=parsed_args.receptor,
                margin=parsed_args.margin,
                exhaustiveness=parsed_args.exhaustiveness,
                num_modes=parsed_args.num_modes,
            )
            config.energy_range = parsed_args.energy_range
            config.seed = parsed_args.seed
            config.cpu = parsed_args.cpu
            config.timeout_seconds = parsed_args.timeout
            config.vina_executable = parsed_args.vina_executable
        elif parsed_args.center:
            cx, cy, cz = parsed_args.center
            sx, sy, sz = parsed_args.size
            config = DockingConfig(
                center_x=cx, center_y=cy, center_z=cz,
                size_x=sx, size_y=sy, size_z=sz,
                exhaustiveness=parsed_args.exhaustiveness,
                num_modes=parsed_args.num_modes,
                energy_range=parsed_args.energy_range,
                seed=parsed_args.seed,
                cpu=parsed_args.cpu,
                timeout_seconds=parsed_args.timeout,
                vina_executable=parsed_args.vina_executable,
            )
        else:
            # Fallback to default or auto-box warning
            config = DockingConfig(
                exhaustiveness=parsed_args.exhaustiveness,
                num_modes=parsed_args.num_modes,
                energy_range=parsed_args.energy_range,
                seed=parsed_args.seed,
                cpu=parsed_args.cpu,
                timeout_seconds=parsed_args.timeout,
                vina_executable=parsed_args.vina_executable,
            )

        config.validate()

        docking = VinaDocking(
            receptor=parsed_args.receptor,
            ligand=parsed_args.ligand,
            config=config,
            output_dir=parsed_args.out_dir,
        )

        result = docking.run(timeout=parsed_args.timeout)

        if parsed_args.save_best and result.poses:
            result.save_best_pose(parsed_args.save_best)

        if parsed_args.json:
            print(result.to_json(indent=2))
        else:
            print("=" * 60)
            print(" BioDockify Vina Docking Results")
            print(" (https://www.biodockify.com)")
            print("=" * 60)
            print(f"Status:             {result.status}")
            print(f"Receptor:           {result.receptor_path}")
            print(f"Ligand:             {result.ligand_path}")
            print(f"Best Affinity:      {result.best_affinity} kcal/mol")
            print(f"Total Modes:        {result.num_poses}")
            print(f"Execution Time:     {result.execution_time_seconds:.2f}s")
            print(f"Output PDBQT:       {result.output_pdbqt_path}")
            print("-" * 60)
            print(f"{'Mode':<6} | {'Affinity (kcal/mol)':<20} | {'RMSD l.b.':<10} | {'RMSD u.b.':<10}")
            print("-" * 60)
            for pose in result.poses:
                print(f"{pose.mode:<6} | {pose.affinity:<20.2f} | {pose.rmsd_lb:<10.3f} | {pose.rmsd_ub:<10.3f}")
            print("=" * 60)
            if parsed_args.save_best:
                print(f"Saved top pose to: {os.path.abspath(parsed_args.save_best)}")

        return 0

    except BiodockifyVinaError as e:
        print(f"BioDockify Vina Error: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
