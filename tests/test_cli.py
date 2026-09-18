import json
import os
import pytest
from unittest.mock import patch, MagicMock
from biodockify_vina.cli import main
from biodockify_vina.models import DockingPose, DockingResult


def test_cli_missing_args(capsys):
    ret = main([])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error: Both --receptor (-r) and --ligand (-l) are required" in captured.err


def test_cli_check_vina_not_found(capsys):
    with patch("biodockify_vina.cli.find_vina_executable", side_effect=Exception("Not found")):
        ret = main(["--check-vina"])
        assert ret == 2


def test_cli_check_vina_found(capsys):
    with patch("biodockify_vina.cli.find_vina_executable", return_value="/usr/bin/vina"):
        ret = main(["--check-vina"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "AutoDock Vina detected: /usr/bin/vina" in captured.out


@patch("biodockify_vina.docking.VinaDocking.run")
def test_cli_docking_execution(mock_run, capsys):
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "examples", "data")
    rec = os.path.join(sample_dir, "sample_receptor.pdbqt")
    lig = os.path.join(sample_dir, "sample_ligand.pdbqt")

    mock_run.return_value = DockingResult(
        status="complete",
        poses=[
            DockingPose(mode=1, affinity=-8.9, rmsd_lb=0.0, rmsd_ub=0.0),
            DockingPose(mode=2, affinity=-8.2, rmsd_lb=1.1, rmsd_ub=2.2),
        ],
        receptor_path=rec,
        ligand_path=lig,
        output_pdbqt_path="out.pdbqt",
        execution_time_seconds=2.34
    )

    ret = main([
        "--receptor", rec,
        "--ligand", lig,
        "--center", "10.0", "20.0", "30.0",
        "--size", "20.0", "20.0", "20.0",
        "--exhaustiveness", "8"
    ])

    assert ret == 0
    captured = capsys.readouterr()
    assert "BioDockify Vina Docking Results" in captured.out
    assert "https://www.biodockify.com" in captured.out
    assert "-8.9" in captured.out


@patch("biodockify_vina.docking.VinaDocking.run")
def test_cli_json_output(mock_run, capsys):
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "examples", "data")
    rec = os.path.join(sample_dir, "sample_receptor.pdbqt")
    lig = os.path.join(sample_dir, "sample_ligand.pdbqt")

    mock_run.return_value = DockingResult(
        status="complete",
        poses=[
            DockingPose(mode=1, affinity=-9.5),
        ],
        receptor_path=rec,
        ligand_path=lig,
        execution_time_seconds=1.2
    )

    ret = main([
        "--receptor", rec,
        "--ligand", lig,
        "--auto-box",
        "--json"
    ])

    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "complete"
    assert data["best_affinity"] == -9.5
    assert data["num_poses"] == 1
