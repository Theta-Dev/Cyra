import os
import shutil
import logging
from importlib_resources import files

DIR_TESTFILES = str(files('tests.testfiles').joinpath(''))
DIR_TMP = os.path.join(DIR_TESTFILES, 'tmp')

logging.basicConfig(level=logging.DEBUG)


def clear_tmp_folder():
    try:
        shutil.rmtree(DIR_TMP)
    except FileNotFoundError:
        pass

    try:
        os.makedirs(DIR_TMP)
    except FileExistsError:
        pass


def assert_files_equal(test, file1, file2):
    with open(file1, 'r') as f:
        c1 = f.read()
    with open(file2, 'r') as f:
        c2 = f.read()
    test.assertEqual(c1, c2)
