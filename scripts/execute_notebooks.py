"""Execute the four notebooks in order, retaining outputs in their source files."""
import os
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
# Kernel discovery must use the active virtual environment, not a system Python.
os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    print("Executing", path.name, flush=True)
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(notebook, timeout=1200, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}})
    client.execute()
    nbformat.write(notebook, path)
print("All four notebooks executed successfully.")
