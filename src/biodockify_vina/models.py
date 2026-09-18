"""
Data models for BioDockify Vina docking results and poses.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json
import os


@dataclass
class DockingPose:
    """Represents a single docked binding mode/pose."""
    mode: int
    affinity: float
    rmsd_lb: float = 0.0
    rmsd_ub: float = 0.0
    pdbqt_content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert pose to a dictionary."""
        return {
            "mode": self.mode,
            "affinity": self.affinity,
            "rmsd_lb": self.rmsd_lb,
            "rmsd_ub": self.rmsd_ub,
            "has_structure": bool(self.pdbqt_content)
        }


@dataclass
class DockingResult:
    """Encapsulates the complete result of an AutoDock Vina docking run."""
    status: str = "complete"
    poses: List[DockingPose] = field(default_factory=list)
    best_affinity: Optional[float] = None
    num_poses: int = 0
    receptor_path: Optional[str] = None
    ligand_path: Optional[str] = None
    output_pdbqt_path: Optional[str] = None
    output_pdbqt_content: Optional[str] = None
    log_text: str = ""
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.poses and self.best_affinity is None:
            self.best_affinity = min(p.affinity for p in self.poses)
        if self.poses and self.num_poses == 0:
            self.num_poses = len(self.poses)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the docking result to a structured dictionary."""
        return {
            "status": self.status,
            "best_affinity": self.best_affinity,
            "num_poses": self.num_poses,
            "poses": [p.to_dict() for p in self.poses],
            "receptor_path": self.receptor_path,
            "ligand_path": self.ligand_path,
            "output_pdbqt_path": self.output_pdbqt_path,
            "execution_time_seconds": round(self.execution_time_seconds, 3),
            "error_message": self.error_message
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize result metadata to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_best_pose(self, filepath: str) -> None:
        """Save the top-ranked (mode 1) pose to a PDBQT file."""
        if not self.poses or not self.poses[0].pdbqt_content:
            raise ValueError("No pose structure content available to save.")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.poses[0].pdbqt_content)
