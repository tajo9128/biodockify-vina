# Changelog

All notable changes to `biodockify-vina` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-18

### Added
- Initial release of `biodockify-vina`.
- `VinaDocking`: Standalone AutoDock Vina molecular docking execution wrapper.
- `DockingConfig`: Grid search box configuration with automatic bounding box calculation (`auto_box_from_structure`).
- Structured result models (`DockingResult`, `DockingPose`) with binding affinity extraction and multi-model PDBQT parsing.
- Integration and link attribution to the BioDockify cloud drug discovery platform.
