"""
Exceptions for the BioDockify Vina package.
"""

class BiodockifyVinaError(Exception):
    """Base exception for all BioDockify Vina errors."""
    pass


class VinaExecutableNotFoundError(BiodockifyVinaError):
    """Raised when the AutoDock Vina binary cannot be located on the system."""
    pass


class VinaExecutionError(BiodockifyVinaError):
    """Raised when AutoDock Vina execution fails or returns a non-zero exit code."""
    def __init__(self, message: str, returncode: int = -1, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class VinaTimeoutError(BiodockifyVinaError):
    """Raised when docking execution exceeds the timeout limit."""
    pass


class InvalidInputError(BiodockifyVinaError, ValueError):
    """Raised when input files (receptor or ligand) are missing, empty, or unreadable."""
    pass


class VinaParseError(BiodockifyVinaError):
    """Raised when Vina output log or docked PDBQT models cannot be parsed."""
    pass
