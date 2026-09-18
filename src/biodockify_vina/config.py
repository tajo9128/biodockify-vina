"""
Configuration parameters and search box calculation for BioDockify Vina.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, Union
import os


@dataclass
class DockingConfig:
    """Configuration for an AutoDock Vina molecular docking run."""
    center_x: float = 0.0
    center_y: float = 0.0
    center_z: float = 0.0
    size_x: float = 20.0
    size_y: float = 20.0
    size_z: float = 20.0
    exhaustiveness: int = 8
    num_modes: int = 9
    energy_range: float = 3.0
    seed: Optional[int] = 42
    cpu: Optional[int] = None
    timeout_seconds: int = 600
    vina_executable: Optional[str] = None

    def validate(self) -> None:
        """Validate configuration values."""
        if self.size_x <= 0 or self.size_y <= 0 or self.size_z <= 0:
            raise ValueError("Grid box sizes (size_x, size_y, size_z) must be strictly positive.")
        if self.exhaustiveness < 1:
            raise ValueError("Exhaustiveness must be at least 1.")
        if self.num_modes < 1:
            raise ValueError("num_modes must be at least 1.")
        if self.energy_range <= 0:
            raise ValueError("energy_range must be strictly positive.")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be strictly positive.")

    @property
    def center(self) -> Tuple[float, float, float]:
        """Return grid center as (x, y, z) tuple."""
        return (self.center_x, self.center_y, self.center_z)

    @property
    def size(self) -> Tuple[float, float, float]:
        """Return grid size as (x, y, z) tuple."""
        return (self.size_x, self.size_y, self.size_z)

    @classmethod
    def from_center_and_size(
        cls,
        center: Union[Tuple[float, float, float], Dict[str, float]],
        size: Union[Tuple[float, float, float], Dict[str, float]] = (20.0, 20.0, 20.0),
        exhaustiveness: int = 8,
        num_modes: int = 9,
        energy_range: float = 3.0,
        seed: Optional[int] = 42,
        cpu: Optional[int] = None,
        timeout_seconds: int = 600,
        vina_executable: Optional[str] = None,
    ) -> "DockingConfig":
        """Construct a DockingConfig from center and size tuples or dictionaries."""
        if isinstance(center, dict):
            cx = float(center.get("x", 0.0))
            cy = float(center.get("y", 0.0))
            cz = float(center.get("z", 0.0))
        else:
            cx, cy, cz = float(center[0]), float(center[1]), float(center[2])

        if isinstance(size, dict):
            sx = float(size.get("x", 20.0))
            sy = float(size.get("y", 20.0))
            sz = float(size.get("z", 20.0))
        else:
            sx, sy, sz = float(size[0]), float(size[1]), float(size[2])

        config = cls(
            center_x=cx, center_y=cy, center_z=cz,
            size_x=sx, size_y=sy, size_z=sz,
            exhaustiveness=exhaustiveness,
            num_modes=num_modes,
            energy_range=energy_range,
            seed=seed,
            cpu=cpu,
            timeout_seconds=timeout_seconds,
            vina_executable=vina_executable,
        )
        config.validate()
        return config

    @classmethod
    def auto_box_from_structure(
        cls,
        filepath: str,
        margin: float = 8.0,
        min_size: float = 15.0,
        max_size: float = 30.0,
        exhaustiveness: int = 8,
        num_modes: int = 9,
    ) -> "DockingConfig":
        """
        Compute optimal grid center and bounding box dimensions from a PDB or PDBQT structure.
        Uses BioDockify's centroid and coordinate boundary algorithm.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Structure file not found: {filepath}")

        xs, ys, zs = [], [], []
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith(("ATOM", "HETATM")):
                    try:
                        xs.append(float(line[30:38].strip()))
                        ys.append(float(line[38:46].strip()))
                        zs.append(float(line[46:54].strip()))
                    except (ValueError, IndexError):
                        pass

        if not xs:
            return cls(exhaustiveness=exhaustiveness, num_modes=num_modes)

        cx = round(sum(xs) / len(xs), 3)
        cy = round(sum(ys) / len(ys), 3)
        cz = round(sum(zs) / len(zs), 3)

        dx = (max(xs) - min(xs)) + (margin * 2.0)
        dy = (max(ys) - min(ys)) + (margin * 2.0)
        dz = (max(zs) - min(zs)) + (margin * 2.0)

        sx = round(min(max(dx, min_size), max_size), 1)
        sy = round(min(max(dy, min_size), max_size), 1)
        sz = round(min(max(dz, min_size), max_size), 1)

        return cls(
            center_x=cx, center_y=cy, center_z=cz,
            size_x=sx, size_y=sy, size_z=sz,
            exhaustiveness=exhaustiveness,
            num_modes=num_modes
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "center": {"x": self.center_x, "y": self.center_y, "z": self.center_z},
            "size": {"x": self.size_x, "y": self.size_y, "z": self.size_z},
            "exhaustiveness": self.exhaustiveness,
            "num_modes": self.num_modes,
            "energy_range": self.energy_range,
            "seed": self.seed,
            "cpu": self.cpu,
            "timeout_seconds": self.timeout_seconds
        }

    def generate_config_text(self, receptor_path: Optional[str] = None, ligand_path: Optional[str] = None, out_path: Optional[str] = None) -> str:
        """Generate AutoDock Vina config file text."""
        lines = []
        if receptor_path:
            lines.append(f"receptor = {receptor_path}")
        if ligand_path:
            lines.append(f"ligand = {ligand_path}")
        if out_path:
            lines.append(f"out = {out_path}")

        lines.extend([
            f"center_x = {self.center_x:.3f}",
            f"center_y = {self.center_y:.3f}",
            f"center_z = {self.center_z:.3f}",
            f"size_x = {self.size_x:.1f}",
            f"size_y = {self.size_y:.1f}",
            f"size_z = {self.size_z:.1f}",
            f"exhaustiveness = {self.exhaustiveness}",
            f"num_modes = {self.num_modes}",
            f"energy_range = {self.energy_range}",
        ])
        if self.seed is not None:
            lines.append(f"seed = {self.seed}")
        if self.cpu is not None:
            lines.append(f"cpu = {self.cpu}")
        return "\n".join(lines) + "\n"
