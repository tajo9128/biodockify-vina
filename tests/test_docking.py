import os
import pytest
from biodockify_vina import VinaDocking, DockingConfig, InvalidInputError


def test_missing_files():
    with pytest.raises(InvalidInputError):
        docking = VinaDocking(
            receptor="non_existent_receptor.pdbqt",
            ligand="non_existent_ligand.pdbqt"
        )
        docking.run()
