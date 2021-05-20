import os
import logging
import tempfile
from importlib_resources import files

DIR_TESTFILES = str(files('tests.testfiles').joinpath(''))
DIR_TESTDOCS = str(files('tests.testdocs').joinpath(''))
DIR_TMP = os.path.join(DIR_TESTFILES, 'tmp')

logging.basicConfig(level=logging.DEBUG)


def tmpdir():
    return tempfile.TemporaryDirectory()


def assert_files_equal(test, file1, file2):
    test.maxDiff = None

    with open(file1, 'r') as f:
        c1 = f.read()
    with open(file2, 'r') as f:
        c2 = f.read()
    test.assertEqual(c1, c2)
