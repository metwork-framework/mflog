# -*- coding: utf-8 -*-

import os
os.environ['_MFLOG_UNITTESTS'] = '1'
import json


from mflog import get_logger
from mflog import UNIT_TESTS_STDOUT, UNIT_TESTS_STDERR, UNIT_TESTS_ADMIN
from mflog import _reset_unittests
import logging


def _test_stdxxx(stdxxx, level, msg, extra=None):
    assert len(stdxxx) == 1
    tmp = stdxxx[0].split("\n")[0].split()
    assert len(tmp) >= 4
    assert len(tmp[0]) == 27
    assert tmp[1] == "[%s]" % level.upper()
    assert tmp[3] == msg
    if extra is not None:
        assert len(tmp) > 4
        assert " ".join(tmp[4:]) == extra
    return tmp


def _test_admin(level, msg):
    assert len(UNIT_TESTS_ADMIN) == 1
    tmp = json.loads(UNIT_TESTS_ADMIN[0])
    assert tmp["level"] == level.lower()
    assert tmp["pid"] > 0
    assert len(tmp["timestamp"]) == 27
    assert tmp['event'] == msg
    return tmp


def test_basic_warning():
    _reset_unittests()
    x = get_logger()
    x.warning("foo")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo")
    _test_admin("WARNING", "foo")


def test_basic_debug():
    _reset_unittests()
    x = get_logger()
    x.debug("foo")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_ADMIN == []
    assert UNIT_TESTS_STDOUT == []


def test_basic_info():
    _reset_unittests()
    x = get_logger()
    x.info("foo")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_ADMIN == []
    _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo")


def test_basic_critical():
    _reset_unittests()
    x = get_logger()
    x.critical("foo")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "CRITICAL", "foo")
    _test_admin("CRITICAL", "foo")


def test_basic_error():
    _reset_unittests()
    x = get_logger()
    x.error("foo")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "ERROR", "foo")
    _test_admin("ERROR", "foo")


def test_basic_exception():
    _reset_unittests()
    x = get_logger()
    try:
        1 / 0
    except Exception:
        x.exception("foo")
    assert UNIT_TESTS_STDOUT == []
    tmp = _test_stdxxx(UNIT_TESTS_STDERR, "ERROR", "foo")
    tmp = _test_admin("ERROR", "foo")
    print(tmp)
    assert len(tmp['exception']) > 10
    assert tmp['exception_type'] == 'ZeroDivisionError'
    assert tmp['exception_file'] == __file__


def test_template_info():
    _reset_unittests()
    x = get_logger()
    x.info("foo%s", "bar")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_ADMIN == []
    _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foobar")


def test_kv_warning():
    _reset_unittests()
    x = get_logger()
    x.warning("foo", k1=1, k2="bar")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo", "{k1=1 k2='bar'}")
    tmp = _test_admin("WARNING", "foo")
    assert tmp['k1'] == 1
    assert tmp['k2'] == 'bar'


def test_utf8():
    _reset_unittests()
    x = get_logger()
    x.warning("fooééé", k1=1, k2="barààà")
    assert UNIT_TESTS_STDOUT == []
    print("********************")
    print(UNIT_TESTS_STDERR)
    print("********************")
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "fooééé", "{k1=1 k2='barààà'}")
    tmp = _test_admin("WARNING", "fooééé")
    assert tmp['k1'] == 1
    assert tmp['k2'] == 'barààà'


def test_bind():
    _reset_unittests()
    x = get_logger("foo.bar")
    x = x.bind(k1=1)
    x = x.bind(k2='bar')
    x.warning("foo")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo", "{k1=1 k2='bar'}")
    tmp = _test_admin("WARNING", "foo")
    assert tmp['k1'] == 1
    assert tmp['k2'] == 'bar'


def test_logging1():
    _reset_unittests()
    x = logging.getLogger("foo.bar")
    x.warning("foo%s", "bar")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foobar")
    _test_admin("WARNING", "foobar")


def test_logging2():
    _reset_unittests()
    x = logging.getLogger()
    x.info("foo")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_ADMIN == []
    _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo")
