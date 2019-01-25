# -*- coding: utf-8 -*-

import os

UNIT_TESTS_MODE = (os.environ.get('_MFLOG_UNITTESTS', '0') == '1')
UNIT_TESTS_STDOUT = []
UNIT_TESTS_STDERR = []
UNIT_TESTS_ADMIN = []


def _reset_unittests():
    """Reset unittests."""
    global UNIT_TESTS_STDOUT, UNIT_TESTS_STDERR, UNIT_TESTS_ADMIN
    del(UNIT_TESTS_STDOUT[:])
    del(UNIT_TESTS_STDERR[:])
    del(UNIT_TESTS_ADMIN[:])
