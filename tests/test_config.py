import pytest
from biodockify_vina.config import DockingConfig


def test_default_config():
    config = DockingConfig()
    assert config.center_x == 0.0
    assert config.size_x == 20.0
    assert config.exhaustiveness == 8
    assert config.num_modes == 9
    assert config.center == (0.0, 0.0, 0.0)
    assert config.size == (20.0, 20.0, 20.0)


def test_from_center_and_size():
    config = DockingConfig.from_center_and_size(
        center=(10.5, -5.2, 33.1),
        size=(15.0, 18.0, 22.0),
        exhaustiveness=16,
        num_modes=5
    )
    assert config.center_x == 10.5
    assert config.center_y == -5.2
    assert config.center_z == 33.1
    assert config.size_x == 15.0
    assert config.exhaustiveness == 16
    assert config.num_modes == 5


def test_invalid_config():
    with pytest.raises(ValueError):
        DockingConfig(size_x=-10.0).validate()

    with pytest.raises(ValueError):
        DockingConfig(exhaustiveness=0).validate()
