import os
import subprocess
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from biodockify_vina import (
    VinaDocking,
    DockingConfig,
    find_vina_executable,
    InvalidInputError,
    VinaExecutionError,
    VinaTimeoutError,
    VinaExecutableNotFoundError,
)

SAMPLE_STDOUT = """
#################################################################
# AutoDock Vina                                                 #
#################################################################

Reading input ... done.
Setting up the scoring function ... done.
Analyzing the binding site ... done.
Using random seed: 42
Performing search ... done.
Refining results ... done.

mode |   affinity | dist from best mode
     | (kcal/mol) | rmsd l.b.| rmsd u.b.
-----+------------+----------+----------
   1         -9.1      0.000      0.000
   2         -8.4      1.240      1.980
   3         -7.8      2.300      3.120
"""

SAMPLE_DOCKED_PDBQT = """MODEL 1
REMARK VINA RESULT:    -9.1      0.000      0.000
ATOM      1  C1  LIG L   1      10.000  20.000  30.000  1.00  0.00    +0.05 C 
ENDMDL
MODEL 2
REMARK VINA RESULT:    -8.4      1.240      1.980
ATOM      1  C1  LIG L   1      11.000  21.000  31.000  1.00  0.00    +0.05 C 
ENDMDL
"""


def test_missing_files():
    with pytest.raises(InvalidInputError, match="Receptor file not found"):
        docking = VinaDocking(
            receptor="non_existent_receptor.pdbqt",
            ligand="non_existent_ligand.pdbqt"
        )
        docking.run()


def test_empty_files():
    with tempfile.NamedTemporaryFile(suffix=".pdbqt", delete=False) as empty_rec:
        empty_rec_path = empty_rec.name
    with tempfile.NamedTemporaryFile(suffix=".pdbqt", delete=False) as empty_lig:
        empty_lig_path = empty_lig.name

    try:
        docking = VinaDocking(receptor=empty_rec_path, ligand=empty_lig_path)
        with pytest.raises(InvalidInputError, match="file is empty"):
            docking.run()
    finally:
        os.remove(empty_rec_path)
        os.remove(empty_lig_path)


@patch("biodockify_vina.docking.find_vina_executable")
@patch("subprocess.run")
def test_successful_docking_execution(mock_subproc, mock_find_vina):
    mock_find_vina.return_value = "/usr/bin/vina"

    # Setup dummy input files
    with tempfile.NamedTemporaryFile(suffix=".pdbqt", mode="w", delete=False) as rf:
        rf.write("ATOM 1 C REC\n")
        rec_path = rf.name
    with tempfile.NamedTemporaryFile(suffix=".pdbqt", mode="w", delete=False) as lf:
        lf.write("ATOM 1 C LIG\n")
        lig_path = lf.name

    with tempfile.TemporaryDirectory() as out_dir:
        # Pre-create docked_output.pdbqt inside the mock run
        def side_effect(*args, **kwargs):
            out_file = os.path.join(out_dir, "docked_output.pdbqt")
            with open(out_file, "w") as f:
                f.write(SAMPLE_DOCKED_PDBQT)
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = SAMPLE_STDOUT
            mock_res.stderr = ""
            return mock_res

        mock_subproc.side_effect = side_effect

        try:
            docking = VinaDocking(
                receptor=rec_path,
                ligand=lig_path,
                center=(12.0, 14.0, 16.0),
                size=(18.0, 18.0, 18.0),
                exhaustiveness=12,
                num_modes=3,
                output_dir=out_dir,
            )

            result = docking.run()

            assert result.status == "complete"
            assert result.best_affinity == -9.1
            assert result.num_poses == 3
            assert result.poses[0].affinity == -9.1
            assert result.poses[1].affinity == -8.4
            assert result.poses[2].affinity == -7.8
            assert result.output_pdbqt_path is not None
            assert os.path.isfile(result.output_pdbqt_path)

            # Check subprocess call arguments
            mock_subproc.assert_called_once()
            call_cmd = mock_subproc.call_args[0][0]
            assert "/usr/bin/vina" in call_cmd
            assert "--receptor" in call_cmd
            assert "--ligand" in call_cmd
            assert "--exhaustiveness" in call_cmd
            assert "12" in call_cmd

        finally:
            os.remove(rec_path)
            os.remove(lig_path)


@patch("biodockify_vina.docking.find_vina_executable")
@patch("subprocess.run")
def test_failed_docking_execution(mock_subproc, mock_find_vina):
    mock_find_vina.return_value = "/usr/bin/vina"

    with tempfile.NamedTemporaryFile(suffix=".pdbqt", mode="w", delete=False) as rf:
        rf.write("ATOM 1 C REC\n")
        rec_path = rf.name
    with tempfile.NamedTemporaryFile(suffix=".pdbqt", mode="w", delete=False) as lf:
        lf.write("ATOM 1 C LIG\n")
        lig_path = lf.name

    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stdout = ""
    mock_res.stderr = "Parse error: syntax error at line 4"
    mock_subproc.return_value = mock_res

    try:
        docking = VinaDocking(receptor=rec_path, ligand=lig_path)
        with pytest.raises(VinaExecutionError) as excinfo:
            docking.run()
        assert excinfo.value.returncode == 1
        assert "Parse error" in str(excinfo.value)
    finally:
        os.remove(rec_path)
        os.remove(lig_path)


@patch("biodockify_vina.docking.find_vina_executable")
@patch("subprocess.run")
def test_docking_timeout(mock_subproc, mock_find_vina):
    mock_find_vina.return_value = "/usr/bin/vina"

    with tempfile.NamedTemporaryFile(suffix=".pdbqt", mode="w", delete=False) as rf:
        rf.write("ATOM 1 C REC\n")
        rec_path = rf.name
    with tempfile.NamedTemporaryFile(suffix=".pdbqt", mode="w", delete=False) as lf:
        lf.write("ATOM 1 C LIG\n")
        lig_path = lf.name

    mock_subproc.side_effect = subprocess.TimeoutExpired(cmd="vina", timeout=5)

    try:
        docking = VinaDocking(receptor=rec_path, ligand=lig_path)
        with pytest.raises(VinaTimeoutError, match="timed out"):
            docking.run(timeout=5)
    finally:
        os.remove(rec_path)
        os.remove(lig_path)


def test_find_vina_executable_not_found():
    with pytest.raises(VinaExecutableNotFoundError):
        find_vina_executable("/non/existent/path/to/custom_vina_executable_12345")
