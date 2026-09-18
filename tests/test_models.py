import os
import json
import pytest
import tempfile
from biodockify_vina.models import DockingPose, DockingResult


def test_docking_pose_to_dict():
    pose = DockingPose(
        mode=1,
        affinity=-8.4,
        rmsd_lb=0.0,
        rmsd_ub=0.0,
        pdbqt_content="MODEL 1\nATOM...\nENDMDL"
    )
    d = pose.to_dict()
    assert d["mode"] == 1
    assert d["affinity"] == -8.4
    assert d["rmsd_lb"] == 0.0
    assert d["rmsd_ub"] == 0.0
    assert d["has_structure"] is True


def test_docking_result_serialization():
    poses = [
        DockingPose(mode=1, affinity=-9.2, rmsd_lb=0.0, rmsd_ub=0.0, pdbqt_content="MODEL 1\nENDMDL"),
        DockingPose(mode=2, affinity=-8.5, rmsd_lb=1.2, rmsd_ub=2.1),
    ]
    result = DockingResult(
        status="complete",
        poses=poses,
        receptor_path="/path/to/receptor.pdbqt",
        ligand_path="/path/to/ligand.pdbqt",
        output_pdbqt_path="/path/to/out.pdbqt",
        execution_time_seconds=1.452
    )

    assert result.best_affinity == -9.2
    assert result.num_poses == 2

    # to_dict
    data = result.to_dict()
    assert data["status"] == "complete"
    assert data["best_affinity"] == -9.2
    assert data["num_poses"] == 2
    assert len(data["poses"]) == 2
    assert data["execution_time_seconds"] == 1.452

    # to_json
    json_str = result.to_json()
    parsed = json.loads(json_str)
    assert parsed["status"] == "complete"
    assert parsed["best_affinity"] == -9.2


def test_save_best_pose():
    poses = [
        DockingPose(mode=1, affinity=-9.2, pdbqt_content="MODEL 1\nATOM 1 C LIG\nENDMDL\n")
    ]
    result = DockingResult(poses=poses)

    with tempfile.TemporaryDirectory() as tmpdir:
        target = os.path.join(tmpdir, "best.pdbqt")
        result.save_best_pose(target)
        assert os.path.isfile(target)
        with open(target, "r") as f:
            content = f.read()
        assert "MODEL 1" in content


def test_save_best_pose_empty_error():
    result = DockingResult(poses=[])
    with pytest.raises(ValueError, match="No pose structure content available"):
        result.save_best_pose("dummy.pdbqt")
