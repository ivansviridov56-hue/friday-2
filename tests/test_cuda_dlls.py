from pathlib import Path

from friday import cuda_dlls


def test_finds_cublas_and_cudnn_bin_dirs(tmp_path: Path) -> None:
    (tmp_path / "cublas" / "bin").mkdir(parents=True)
    (tmp_path / "cudnn" / "bin").mkdir(parents=True)

    found = cuda_dlls.find_cuda_dll_dirs([str(tmp_path)])

    assert found == [tmp_path / "cublas" / "bin", tmp_path / "cudnn" / "bin"]


def test_returns_empty_when_nothing_installed(tmp_path: Path) -> None:
    assert cuda_dlls.find_cuda_dll_dirs([str(tmp_path)]) == []


def test_add_prepends_to_path(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "cublas" / "bin").mkdir(parents=True)
    monkeypatch.setenv("PATH", "original")
    monkeypatch.setattr("os.add_dll_directory", lambda p: None, raising=False)

    cuda_dlls.add_cuda_dll_dirs([str(tmp_path)])

    import os

    assert os.environ["PATH"].startswith(str(tmp_path / "cublas" / "bin"))
    assert os.environ["PATH"].endswith("original")
