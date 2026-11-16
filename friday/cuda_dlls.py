"""Make pip-installed NVIDIA DLLs (cuBLAS, cuDNN) visible to CTranslate2 on Windows."""

from __future__ import annotations

import importlib.util
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

_SUBPACKAGES = ("cublas", "cudnn")


def find_cuda_dll_dirs(search_roots: list[str] | None = None) -> list[Path]:
    """Return existing `bin` dirs of the pip-installed NVIDIA packages."""
    if search_roots is None:
        spec = importlib.util.find_spec("nvidia")
        search_roots = list(spec.submodule_search_locations or []) if spec else []
    dirs: list[Path] = []
    for root in search_roots:
        for sub in _SUBPACKAGES:
            bin_dir = Path(root) / sub / "bin"
            if bin_dir.is_dir():
                dirs.append(bin_dir)
    return dirs


def add_cuda_dll_dirs(search_roots: list[str] | None = None) -> list[Path]:
    """Register the found dirs for DLL loading and return them."""
    dirs = find_cuda_dll_dirs(search_roots)
    for bin_dir in dirs:
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(bin_dir))
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ["PATH"]
        log.debug("added CUDA DLL dir: %s", bin_dir)
    return dirs
