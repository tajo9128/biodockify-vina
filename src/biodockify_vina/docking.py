"""
Core AutoDock Vina docking execution engine and output parser for BioDockify Vina.
"""

import os
import re
import shutil
import subprocess
import time
import tempfile
from typing import Optional, List, Dict, Tuple, Union, Any

from .models import DockingPose, DockingResult
from .config import DockingConfig
from .exceptions import (
    BiodockifyVinaError,
    VinaExecutableNotFoundError,
    VinaExecutionError,
    VinaTimeoutError,
    InvalidInputError,
    VinaParseError,
)


def find_vina_executable(custom_path: Optional[str] = None) -> str:
    """Locate the AutoDock Vina executable on the system."""
    if custom_path:
        if os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
            return custom_path
        which_custom = shutil.which(custom_path)
        if which_custom:
            return which_custom
        raise VinaExecutableNotFoundError(f"Specified Vina executable not found or not executable: {custom_path}")

    env_path = os.getenv("VINA_EXECUTABLE")
    if env_path and os.path.isfile(env_path):
        return env_path

    candidates = ["vina", "vina.exe", "autodock_vina", "autodock_vina.exe"]
    for c in candidates:
        found = shutil.which(c)
        if found:
            return found

    common_search_paths = [
        r"C:\Program Files\The Scripps Research Institute\Vina\vina.exe",
        r"C:\Program Files (x86)\The Scripps Research Institute\Vina\vina.exe",
        r"C:\vina\vina.exe",
        "/usr/bin/vina",
        "/usr/local/bin/vina",
        "/opt/vina/bin/vina",
        "/opt/biodockify/bin/vina",
    ]
    for p in common_search_paths:
        if os.path.isfile(p):
            return p

    raise VinaExecutableNotFoundError(
        "AutoDock Vina executable ('vina') was not found on your PATH or common locations. "
        "Please install AutoDock Vina (e.g. 'conda install -c conda-forge vina' or download from "
        "https://vina.scripps.edu) and ensure 'vina' is in your PATH, or pass vina_executable to DockingConfig."
    )


def parse_vina_energy_table(stdout: str) -> List[Dict[str, Any]]:
    """Parse Vina affinity table from stdout or log file."""
    lines = stdout.split("\n")
    table_start = -1
    for i, line in enumerate(lines):
        if "mode" in line.lower() and "affinity" in line.lower():
            table_start = i + 1
            break
        if "-----+" in line:
            table_start = i + 1
            break

    entries = []
    if table_start >= 0:
        for line in lines[table_start:]:
            stripped = line.strip()
            if not stripped:
                break
            parts = stripped.split()
            if len(parts) >= 2:
                try:
                    entries.append({
                        "mode": int(parts[0]),
                        "affinity": float(parts[1]),
                        "rmsd_lb": float(parts[2]) if len(parts) >= 3 else 0.0,
                        "rmsd_ub": float(parts[3]) if len(parts) >= 4 else 0.0,
                    })
                except (ValueError, IndexError):
                    pass
    return entries


def parse_docked_pdbqt_models(pdbqt_content: str) -> List[str]:
    """Split multi-model PDBQT output into individual model PDBQT strings."""
    models = []
    current = []
    in_model = False

    for line in pdbqt_content.split("\n"):
        if line.startswith("MODEL"):
            in_model = True
            current = [line]
        elif line.startswith("ENDMDL"):
            current.append(line)
            models.append("\n".join(current) + "\n")
            current = []
            in_model = False
        elif in_model:
            current.append(line)

    if not models and pdbqt_content.strip():
        models.append(pdbqt_content)

    return models


class VinaDocking:
    """
    High-level AutoDock Vina molecular docking runner.
    
    Example:
        >>> docking = VinaDocking(
        ...     receptor="receptor.pdbqt",
        ...     ligand="ligand.pdbqt",
        ...     center=(10.0, 12.0, 15.0),
        ...     size=(20.0, 20.0, 20.0),
        ...     exhaustiveness=8
        ... )
        >>> result = docking.run()
        >>> print(f"Best affinity: {result.best_affinity} kcal/mol")
    """

    def __init__(
        self,
        receptor: str,
        ligand: str,
        config: Optional[DockingConfig] = None,
        center: Optional[Union[Tuple[float, float, float], Dict[str, float]]] = None,
        size: Optional[Union[Tuple[float, float, float], Dict[str, float]]] = None,
        exhaustiveness: int = 8,
        num_modes: int = 9,
        energy_range: float = 3.0,
        seed: Optional[int] = 42,
        cpu: Optional[int] = None,
        output_dir: Optional[str] = None,
        vina_executable: Optional[str] = None,
    ):
        self.receptor = receptor
        self.ligand = ligand
        self.output_dir = output_dir

        if config is not None:
            self.config = config
        else:
            if center is not None:
                self.config = DockingConfig.from_center_and_size(
                    center=center,
                    size=size or (20.0, 20.0, 20.0),
                    exhaustiveness=exhaustiveness,
                    num_modes=num_modes,
                    energy_range=energy_range,
                    seed=seed,
                    cpu=cpu,
                    vina_executable=vina_executable
                )
            else:
                self.config = DockingConfig(
                    exhaustiveness=exhaustiveness,
                    num_modes=num_modes,
                    energy_range=energy_range,
                    seed=seed,
                    cpu=cpu,
                    vina_executable=vina_executable
                )

        self.config.validate()

    def run(self, timeout: Optional[int] = None) -> DockingResult:
        """Execute AutoDock Vina docking and return structured DockingResult."""
        if not os.path.isfile(self.receptor):
            raise InvalidInputError(f"Receptor file not found: {self.receptor}")
        if not os.path.isfile(self.ligand):
            raise InvalidInputError(f"Ligand file not found: {self.ligand}")

        if os.path.getsize(self.receptor) == 0:
            raise InvalidInputError(f"Receptor file is empty: {self.receptor}")
        if os.path.getsize(self.ligand) == 0:
            raise InvalidInputError(f"Ligand file is empty: {self.ligand}")

        vina_exe = find_vina_executable(self.config.vina_executable)
        timeout_sec = timeout or self.config.timeout_seconds

        work_dir = self.output_dir or tempfile.mkdtemp(prefix="biodockify_vina_")
        os.makedirs(work_dir, exist_ok=True)

        out_pdbqt_path = os.path.join(work_dir, "docked_output.pdbqt")
        log_path = os.path.join(work_dir, "vina_log.txt")

        cmd = [
            vina_exe,
            "--receptor", os.path.abspath(self.receptor),
            "--ligand", os.path.abspath(self.ligand),
            "--out", out_pdbqt_path,
            "--center_x", str(self.config.center_x),
            "--center_y", str(self.config.center_y),
            "--center_z", str(self.config.center_z),
            "--size_x", str(self.config.size_x),
            "--size_y", str(self.config.size_y),
            "--size_z", str(self.config.size_z),
            "--exhaustiveness", str(self.config.exhaustiveness),
            "--num_modes", str(self.config.num_modes),
            "--energy_range", str(self.config.energy_range),
        ]

        if self.config.seed is not None:
            cmd.extend(["--seed", str(self.config.seed)])
        if self.config.cpu is not None:
            cmd.extend(["--cpu", str(self.config.cpu)])

        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
        except subprocess.TimeoutExpired as e:
            raise VinaTimeoutError(f"Docking execution timed out after {timeout_sec} seconds.") from e
        except Exception as e:
            raise VinaExecutionError(f"Failed to execute Vina subprocess: {e}") from e

        duration = time.time() - start_time
        combined_log = proc.stdout
        if proc.stderr:
            combined_log += "\nSTDERR:\n" + proc.stderr

        try:
            with open(log_path, "w", encoding="utf-8") as lf:
                lf.write(combined_log)
        except Exception:
            pass

        if proc.returncode != 0:
            raise VinaExecutionError(
                f"AutoDock Vina failed with exit code {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}",
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr
            )

        # Parse log table
        table_entries = parse_vina_energy_table(proc.stdout)

        # Read docked PDBQT
        pdbqt_content = ""
        model_blocks = []
        if os.path.isfile(out_pdbqt_path):
            with open(out_pdbqt_path, "r", encoding="utf-8", errors="replace") as f:
                pdbqt_content = f.read()
            model_blocks = parse_docked_pdbqt_models(pdbqt_content)

        poses: List[DockingPose] = []
        if table_entries:
            for idx, entry in enumerate(table_entries):
                pose_content = model_blocks[idx] if idx < len(model_blocks) else None
                poses.append(
                    DockingPose(
                        mode=entry["mode"],
                        affinity=entry["affinity"],
                        rmsd_lb=entry.get("rmsd_lb", 0.0),
                        rmsd_ub=entry.get("rmsd_ub", 0.0),
                        pdbqt_content=pose_content
                    )
                )
        elif model_blocks:
            for idx, block in enumerate(model_blocks):
                energy = None
                for line in block.split("\n"):
                    if "REMARK VINA RESULT:" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                energy = float(parts[3])
                            except ValueError:
                                pass
                poses.append(
                    DockingPose(
                        mode=idx + 1,
                        affinity=energy if energy is not None else 0.0,
                        pdbqt_content=block
                    )
                )

        poses.sort(key=lambda p: p.affinity)

        return DockingResult(
            status="complete",
            poses=poses,
            best_affinity=poses[0].affinity if poses else None,
            num_poses=len(poses),
            receptor_path=os.path.abspath(self.receptor),
            ligand_path=os.path.abspath(self.ligand),
            output_pdbqt_path=out_pdbqt_path if os.path.isfile(out_pdbqt_path) else None,
            output_pdbqt_content=pdbqt_content or None,
            log_text=combined_log,
            execution_time_seconds=duration,
        )
