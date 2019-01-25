# -*- coding: utf-8 -*-

import os

UNIT_TESTS_MODE = (os.environ.get('_MFLOG_UNITTESTS', '0') == '1')
UNIT_TESTS_STDOUT = []
UNIT_TESTS_STDERR = []
UNIT_TESTS_ADMIN = []


def _reset_unittests():
    """Reset unittests."""
    global UNIT_TESTS_STDOUT, UNIT_TESTS_STDERR, UNIT_TESTS_ADMIN
    UNIT_TESTS_STDOUT.clear()
    UNIT_TESTS_STDERR.clear()
    UNIT_TESTS_ADMIN.clear()
