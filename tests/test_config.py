import os
import pytest
from biodockify_vina.config import DockingConfig


def test_default_config():
    config = DockingConfig()
    assert config.center_x == 0.0
    assert config.size_x == 20.0
    assert config.exhaustiveness == 8
    assert config.num_modes == 9
    assert config.energy_range == 3.0
    assert config.center == (0.0, 0.0, 0.0)
    assert config.size == (20.0, 20.0, 20.0)


def test_from_center_and_size_tuples():
    config = DockingConfig.from_center_and_size(
        center=(10.5, -5.2, 33.1),
        size=(15.0, 18.0, 22.0),
        exhaustiveness=16,
        num_modes=5,
        energy_range=2.5,
        seed=123,
        cpu=4,
    )
    assert config.center_x == 10.5
    assert config.center_y == -5.2
    assert config.center_z == 33.1
    assert config.size_x == 15.0
    assert config.exhaustiveness == 16
    assert config.num_modes == 5
    assert config.energy_range == 2.5
    assert config.seed == 123
    assert config.cpu == 4


def test_from_center_and_size_dicts():
    config = DockingConfig.from_center_and_size(
        center={"x": 5.0, "y": 6.0, "z": 7.0},
        size={"x": 25.0, "y": 25.0, "z": 25.0}
    )
    assert config.center == (5.0, 6.0, 7.0)
    assert config.size == (25.0, 25.0, 25.0)


def test_invalid_config_validations():
    with pytest.raises(ValueError, match="strictly positive"):
        DockingConfig(size_x=-10.0).validate()

    with pytest.raises(ValueError, match="strictly positive"):
        DockingConfig(size_y=0.0).validate()

    with pytest.raises(ValueError, match="at least 1"):
        DockingConfig(exhaustiveness=0).validate()

    with pytest.raises(ValueError, match="at least 1"):
        DockingConfig(num_modes=0).validate()

    with pytest.raises(ValueError, match="energy_range"):
        DockingConfig(energy_range=-1.0).validate()

    with pytest.raises(ValueError, match="timeout_seconds"):
        DockingConfig(timeout_seconds=0).validate()


def test_auto_box_from_structure():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "examples", "data", "sample_receptor.pdbqt")
    config = DockingConfig.auto_box_from_structure(sample_path, margin=6.0)
    assert config.center_x == 15.514
    assert config.center_y == 20.671
    assert config.center_z == 12.04
    assert config.size_x > 15.0
    assert config.size_y > 15.0
    assert config.size_z > 15.0


def test_auto_box_missing_file():
    with pytest.raises(FileNotFoundError):
        DockingConfig.auto_box_from_structure("non_existent_structure.pdbqt")


def test_to_dict():
    config = DockingConfig(center_x=1.0, center_y=2.0, center_z=3.0)
    d = config.to_dict()
    assert d["center"] == {"x": 1.0, "y": 2.0, "z": 3.0}
    assert d["size"] == {"x": 20.0, "y": 20.0, "z": 20.0}
    assert d["exhaustiveness"] == 8


def test_generate_config_text():
    config = DockingConfig(center_x=10.0, center_y=15.0, center_z=20.0, seed=99, cpu=2)
    text = config.generate_config_text(receptor_path="rec.pdbqt", ligand_path="lig.pdbqt", out_path="out.pdbqt")
    assert "receptor = rec.pdbqt" in text
    assert "ligand = lig.pdbqt" in text
    assert "out = out.pdbqt" in text
    assert "center_x = 10.000" in text
    assert "seed = 99" in text
    assert "cpu = 2" in text
