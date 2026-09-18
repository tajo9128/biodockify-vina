import json
from biodockify_vina.models import DockingPose, DockingResult


def test_docking_pose():
    pose = DockingPose(mode=1, affinity=-8.4, rmsd_lb=0.0, rmsd_ub=0.0, pdbqt_content="ATOM...")
    d = pose.to_dict()
    assert d["mode"] == 1
    assert d["affinity"] == -8.4
    assert d["has_structure"] is True


def test_docking_result():
    poses = [
        DockingPose(mode=1, affinity=-9.2),
        DockingPose(mode=2, affinity=-8.5, rmsd_lb=1.2, rmsd_ub=2.1),
    ]
    result = DockingResult(
        status="complete",
        poses=poses,
        execution_time_seconds=1.45
    )
    assert result.best_affinity == -9.2
    assert result.num_poses == 2
    data = result.to_dict()
    assert data["best_affinity"] == -9.2
    assert len(data["poses"]) == 2
