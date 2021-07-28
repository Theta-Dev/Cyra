import os
import logging
from importlib_resources import files

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory


DIR_TESTFILES = str(files('tests').joinpath('testfiles'))
DIR_TESTDOCS = str(files('tests').joinpath('testdocs'))
DIR_TMP = os.path.join(DIR_TESTFILES, 'tmp')

logging.basicConfig(level=logging.DEBUG)


def tmpdir():
    return TemporaryDirectory()


def assert_files_equal(test, file1, file2):
    test.maxDiff = None

    with open(file1, 'r') as f:
        c1 = f.read()
    with open(file2, 'r') as f:
        c2 = f.read()
    test.assertEqual(c1, c2)
