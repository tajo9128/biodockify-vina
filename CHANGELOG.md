# Changelog

All notable changes to `biodockify-vina` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-09-18

### Added
- **Command-Line Interface (CLI)**: Added `biodockify-vina` CLI entrypoint and `python -m biodockify_vina` support with rich tabular results formatting and `--json` pipeline mode.
- **Auto-Box CLI Integration**: Added `--auto-box` and `--margin` CLI flags for automated pocket detection directly from structure files.
- **Sample Benchmark Data**: Added `examples/data/sample_receptor.pdbqt` and `sample_ligand.pdbqt` alongside runnable scripts `quickstart.py` and `auto_box_example.py`.
- **PEP 561 Type Compliance**: Added `py.typed` marker for static type checking in mypy and IDEs.
- **Comprehensive Test Suite**: Expanded unit tests to 29 comprehensive test cases with mocked subprocesses, error simulations, and CLI testing.

## [0.1.0] - 2026-09-18

### Added
- Initial release of `biodockify-vina`.
- `VinaDocking`: Standalone AutoDock Vina molecular docking execution wrapper.
- `DockingConfig`: Grid search box configuration with automatic bounding box calculation (`auto_box_from_structure`).
- Structured result models (`DockingResult`, `DockingPose`) with binding affinity extraction and multi-model PDBQT parsing.
- Integration and link attribution to the BioDockify cloud drug discovery platform.
