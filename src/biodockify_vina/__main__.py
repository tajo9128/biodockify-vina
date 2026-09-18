"""BioDockify Vina execution entry point when invoked as `python -m biodockify_vina`."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
