# -*- coding: utf-8 -*-

import os
import mflog

UNIT_TESTS_MODE = (os.environ.get('_MFLOG_UNITTESTS', '0') == '1')
UNIT_TESTS_STDOUT = []
UNIT_TESTS_STDERR = []
UNIT_TESTS_JSON = []


def reset_unittests():
    """Reset unittests."""
    global UNIT_TESTS_STDOUT, UNIT_TESTS_STDERR, UNIT_TESTS_JSON
    del(UNIT_TESTS_STDOUT[:])
    del(UNIT_TESTS_STDERR[:])
    del(UNIT_TESTS_JSON[:])
    try:
        del(os.environ["MFLOG_EXTRA_CONTEXT_FUNC"])
    except Exception:
        pass
    try:
        del(os.environ["MFLOG_JSON_ONLY_KEYS"])
    except Exception:
        pass
    mflog.__unset_configuration()


def extra_context():
    return {"extra_context_key1": "extra_context_value1",
            "extra_context_key2": "extra_context_value2"}
