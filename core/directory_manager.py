from pathlib import Path
import shutil
import os
from typing import List, Dict
from datetime import datetime


class DirectoryManager:
    """
    Manages directory structure for a FORCAsT objective and its runs.

    Structure:

    OBJECTIVE_ROOT/
        forcast.exe
        runs/
            run_name/
                forcast.exe (symlink)
                inputn
                out/
                data/
                fd2dat/
    """

    def __init__(self, objective_root, executable_name="forcast.exe"):
        self.objective_root = Path(objective_root).expanduser().resolve()
        self.executable_name = executable_name

        self.executable_path = self.objective_root / executable_name
        self.runs_dir = self.objective_root / "runs"

        self._initialize_objective_structure()

        self.current_run_dir = None

    # --------------------------------------------------
    # OBJECTIVE LEVEL
    # --------------------------------------------------

    def _initialize_objective_structure(self):
        """
        Create objective root and runs directory.
        Ensure executable exists.
        """
        self.objective_root.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        if not self.executable_path.exists():
            raise FileNotFoundError(
                f"FORCAsT executable not found at {self.executable_path}"
            )

    def list_runs(self, detailed: bool = False) -> List:
        """
        List all available model runs.

        Parameters
        ----------
        detailed : bool
            If True, returns metadata (size, creation time, etc.)
            If False, returns only run names.

        Returns
        -------
        List[str] or List[Dict]
        """

        if not self.runs_dir.exists():
            return []

        run_dirs = sorted(
            [d for d in self.runs_dir.iterdir() if d.is_dir()]
        )

        if not detailed:
            return [d.name for d in run_dirs]

        runs_info = []
        for d in run_dirs:
            stat = d.stat()
            runs_info.append({
                "name": d.name,
                "path": str(d),
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "size_mb": self._get_directory_size(d) / (1024 * 1024)
            })

        return runs_info

    # --------------------------------------------------
    # RUN LEVEL
    # --------------------------------------------------

    def create_run(self, run_name):
        """
        Create a new run directory with required structure.
        Also copies fd2dat files from objective_root into the run.
        """

        run_dir = self.runs_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        # Required subdirectories
        out_dir = run_dir / "out"
        data_dir = run_dir / "data"
        run_fd2dat_dir = run_dir / "fd2dat"

        out_dir.mkdir(exist_ok=True)
        data_dir.mkdir(exist_ok=True)
        run_fd2dat_dir.mkdir(exist_ok=True)

        # --------------------------------------------------
        # Copy fd2dat contents from objective_root
        # --------------------------------------------------
        source_fd2dat_dir = self.objective_root / "fd2dat"

        if source_fd2dat_dir.exists():
            for item in source_fd2dat_dir.iterdir():
                src = item
                dst = run_fd2dat_dir / item.name

                if item.is_dir():
                    # Recursively copy subdirectories
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        else:
            raise FileNotFoundError(
                f"fd2dat directory not found in objective_root: {source_fd2dat_dir}"
            )

        # --------------------------------------------------
        # Create symlink to executable
        # --------------------------------------------------
        run_exe = run_dir / self.executable_name

        if not run_exe.exists():
            try:
                os.symlink(self.executable_path, run_exe)
            except OSError:
                # Windows fallback: copy executable
                shutil.copy2(self.executable_path, run_exe)

        self.current_run_dir = run_dir
        return run_dir

    def load_run(self, run_name, model_class, **kwargs):
        """
        Reconstruct a ForcastModel from a stored run.
    
        Parameters
        ----------
        run_name : str
            Name of run directory
        model_class : class
            ForcastModel class

    
        Returns
        -------
        ForcastModel instance
        """
    
        run_dir = self.get_run_dir()
    
        if not run_dir.exists():
            raise ValueError(f"Run '{run_name}' does not exist.")
    
        input_file = self.get_input_file()
    
        if not input_file.exists():
            raise FileNotFoundError("input.dat not found in run directory.")
    
        # Delegate reconstruction to model class
        model = model_class.from_input_file(
            input_file,
            self,
            run_dir,
            **kwargs,
        )
    
        return model    

    # --------------------------------------------------
    # PATH GETTERS
    # --------------------------------------------------

    def get_run_dir(self):
        self._ensure_run_selected()
        return self.current_run_dir

    def get_input_file(self):
        self._ensure_run_selected()
        return self.current_run_dir / "inputn"

    def get_out_dir(self):
        self._ensure_run_selected()
        return self.current_run_dir / "out"

    def get_data_dir(self):
        self._ensure_run_selected()
        return self.current_run_dir / "data"

    def get_fd2dat_dir(self):
        self._ensure_run_selected()
        return self.current_run_dir / "fd2dat"

    def get_executable(self):
        self._ensure_run_selected()
        return self.current_run_dir / self.executable_name

    def _ensure_run_selected(self):
        if self.current_run_dir is None:
            raise RuntimeError("No run has been created. Call create_run() first.")

    def _get_directory_size(self, path: Path) -> int:
        """
        Recursively compute directory size in bytes.
        """
        total = 0
        for p in path.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
        return total

