# BioDockify Vina (`biodockify-vina`)

[![PyPI version](https://img.shields.io/pypi/v/biodockify-vina.svg)](https://pypi.org/project/biodockify-vina/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/biodockify-vina.svg)](https://pypi.org/project/biodockify-vina/)
[![Platform](https://img.shields.io/badge/BioDockify-Platform-blue)](https://www.biodockify.com/)

**`biodockify-vina`** provides a clean, robust, and standalone Python workflow & CLI for single-molecule molecular docking using [AutoDock Vina](https://vina.scripps.edu/).

Developed and maintained by the **[BioDockify](https://www.biodockify.com/)** team, this package encapsulates the battle-tested single-docking execution, automatic bounding box calculation, multi-model coordinate parsing, and energy extraction engine from the BioDockify computational drug discovery platform.

---

## 🔬 About BioDockify

**[BioDockify](https://www.biodockify.com/)** is an AI-powered cloud-native pharmaceutical research platform providing automated molecular docking, GPU-accelerated molecular dynamics (MD) simulations, 3D QSAR modeling, ADMET property prediction, and autonomous drug discovery copilots for researchers worldwide.

- **Website**: [https://www.biodockify.com/](https://www.biodockify.com/)
- **Online Molecular Docking**: [https://www.biodockify.com/molecular-docking-online](https://www.biodockify.com/molecular-docking-online)
- **Documentation**: [https://www.biodockify.com/docs](https://www.biodockify.com/docs)
- **GitHub**: [https://github.com/tajo9128/biodockify-vina](https://github.com/tajo9128/biodockify-vina)

---

## 📦 Prerequisites & AutoDock Vina Requirement

`biodockify-vina` coordinates input preparation, grid configuration, process execution, and output parsing. It requires an **AutoDock Vina** executable binary installed on your system.

### Installing AutoDock Vina:
- **Conda (Recommended)**:
  ```bash
  conda install -c conda-forge vina
  ```
- **Ubuntu / Debian**:
  ```bash
  sudo apt-get install autodock-vina
  ```
- **Direct Binary Download**:
  Download the official pre-compiled binary for Windows, macOS, or Linux from the [Center for Computational Structural Biology (CCSB)](https://vina.scripps.edu/downloads/) and add `vina` to your system `PATH`.

You can verify your Vina installation at any time:
```bash
biodockify-vina --check-vina
```

---

## 🚀 Installation

```bash
pip install biodockify-vina
```

---

## 💻 Command-Line Interface (CLI)

`biodockify-vina` includes a full-featured CLI:

### 1. Basic Docking Run
```bash
biodockify-vina \
  --receptor examples/data/sample_receptor.pdbqt \
  --ligand examples/data/sample_ligand.pdbqt \
  --center 15.5 20.7 12.0 \
  --size 20.0 20.0 20.0 \
  --exhaustiveness 8 \
  --save-best top_pose.pdbqt
```

### 2. Automated Search Box Detection (`--auto-box`)
Automatically compute the pocket centroid and search dimensions directly from receptor coordinates:
```bash
biodockify-vina \
  -r examples/data/sample_receptor.pdbqt \
  -l examples/data/sample_ligand.pdbqt \
  --auto-box \
  --json
```

---

## ⚡ Python API Quick Start

### 1. Basic Docking Run

```python
from biodockify_vina import VinaDocking

# Initialize and run docking
docking = VinaDocking(
    receptor="receptor.pdbqt",
    ligand="ligand.pdbqt",
    center=(15.2, 24.8, 11.4),
    size=(20.0, 20.0, 20.0),
    exhaustiveness=8,
    num_modes=9
)

result = docking.run()

print(f"Status: {result.status}")
print(f"Best Binding Affinity: {result.best_affinity} kcal/mol")
print(f"Total Modes Generated: {result.num_poses}")

# Iterate through binding modes
for pose in result.poses:
    print(f"Mode {pose.mode}: {pose.affinity} kcal/mol (RMSD: lb={pose.rmsd_lb}, ub={pose.rmsd_ub})")

# Save top-ranked pose
result.save_best_pose("best_docked_pose.pdbqt")

# Export to JSON
print(result.to_json(indent=2))
```

### 2. Automatic Grid Box Calculation

```python
from biodockify_vina import VinaDocking, DockingConfig

# Automatically compute grid center and bounding dimensions from receptor structure
config = DockingConfig.auto_box_from_structure("receptor.pdbqt", margin=8.0)

docking = VinaDocking(
    receptor="receptor.pdbqt",
    ligand="ligand.pdbqt",
    config=config
)

result = docking.run()
print(f"Docked with auto-box center {config.center} and size {config.size}")
```

---

## ⚙️ Configuration Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `receptor` | `str` | *required* | Path to the receptor structure in PDBQT format |
| `ligand` | `str` | *required* | Path to the ligand structure in PDBQT format |
| `center` | `tuple / dict` | `(0, 0, 0)` | Search box center `(center_x, center_y, center_z)` in Ångströms |
| `size` | `tuple / dict` | `(20, 20, 20)`| Search box dimensions `(size_x, size_y, size_z)` in Ångströms |
| `exhaustiveness`| `int` | `8` | Search exhaustiveness (higher = more thorough search) |
| `num_modes` | `int` | `9` | Maximum number of binding modes to output |
| `energy_range` | `float` | `3.0` | Maximum energy difference between best and worst mode (kcal/mol) |
| `seed` | `int` | `42` | Random seed for reproducible docking results |
| `cpu` | `int` | `None` | Number of CPU cores to utilize (default: auto-detect all available) |
| `timeout_seconds`| `int` | `600` | Maximum execution time in seconds before raising `VinaTimeoutError` |
| `vina_executable`| `str` | `None` | Path to custom AutoDock Vina binary |

---

## 🧪 Output Description

The `DockingResult` object contains:
- `status`: Execution status (`complete` or `error`).
- `best_affinity`: Top binding affinity in kcal/mol (most negative score).
- `num_poses`: Number of generated binding poses.
- `poses`: List of `DockingPose` objects containing `mode`, `affinity`, `rmsd_lb`, `rmsd_ub`, and `pdbqt_content`.
- `output_pdbqt_path`: Path to the generated multi-model PDBQT output file.
- `log_text`: Full stdout log from the AutoDock Vina run.
- `execution_time_seconds`: Total wall-clock time consumed by the docking computation.

---

## 🛠️ Development & Testing

Clone the repository and install development dependencies:

```bash
git clone https://github.com/tajo9128/biodockify-vina.git
cd biodockify-vina
pip install -e ".[dev]"
pytest -v
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

AutoDock Vina is developed by the Center for Computational Structural Biology (CCSB) at The Scripps Research Institute and is licensed under the Apache 2.0 License.
