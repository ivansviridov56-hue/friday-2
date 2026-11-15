import sys

import friday


def test_python_version():
    assert sys.version_info >= (3, 11)


def test_package_imports():
    assert friday is not None
