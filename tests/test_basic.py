# -*- coding: utf-8 -*-

import pytest
import sys

import force_unittests_mode  # noqa: F401
import json
from mflog import get_logger, set_config
from mflog import UNIT_TESTS_STDOUT, UNIT_TESTS_STDERR, UNIT_TESTS_JSON
from mflog.unittests import reset_unittests
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


def _test_json(level, msg):
    assert len(UNIT_TESTS_JSON) == 1
    tmp = json.loads(UNIT_TESTS_JSON[0])
    assert tmp["level"] == level.lower()
    assert tmp["pid"] > 0
    assert len(tmp["timestamp"]) == 27
    assert tmp['event'] == msg
    return tmp


def test_basic_warning():
    reset_unittests()
    x = get_logger()
    x.warning("foo")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo")
    _test_json("WARNING", "foo")


def test_basic_debug():
    reset_unittests()
    x = get_logger()
    x.debug("foo")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    assert UNIT_TESTS_STDOUT == []


def test_basic_info():
    reset_unittests()
    x = get_logger()
    x.info("foo")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo")


def test_basic_critical():
    reset_unittests()
    x = get_logger()
    x.critical("foo")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "CRITICAL", "foo")
    _test_json("CRITICAL", "foo")


def test_basic_error():
    reset_unittests()
    x = get_logger()
    x.error("foo")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "ERROR", "foo")
    _test_json("ERROR", "foo")


def test_basic_exception():
    reset_unittests()
    x = get_logger()
    try:
        1 / 0
    except Exception:
        x.exception("foo")
    assert UNIT_TESTS_STDOUT == []
    tmp = _test_stdxxx(UNIT_TESTS_STDERR, "ERROR", "foo")
    tmp = _test_json("ERROR", "foo")
    assert len(tmp['exception']) > 10
    assert tmp['exception_type'] == 'ZeroDivisionError'
    assert tmp['exception_file'] == __file__


def test_template_info():
    reset_unittests()
    x = get_logger()
    x.info("foo%s", "bar")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foobar")


def test_kv_warning():
    reset_unittests()
    x = get_logger()
    x.warning("foo", k1=1, k2="bar")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo", "{k1=1 k2=bar}")
    tmp = _test_json("WARNING", "foo")
    assert tmp['k1'] == 1
    assert tmp['k2'] == 'bar'


def test_utf8():
    reset_unittests()
    x = get_logger()
    x.warning(u"fooééé", k1=1, k2=u"barààà")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", u"fooééé", u"{k1=1 k2=barààà}")
    tmp = _test_json("WARNING", u"fooééé")
    assert tmp['k1'] == 1
    assert tmp['k2'] == u'barààà'


@pytest.mark.skipif(sys.version_info < (3, 0), reason="requires python3")
def test_bytes():
    reset_unittests()
    x = get_logger()
    x.warning(b"foo", k1=1, k2=b"bar")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo", "{k1=1 k2=bar}")
    tmp = _test_json("WARNING", "foo")
    assert tmp['k1'] == 1
    assert tmp['k2'] == 'bar'


def test_bind():
    reset_unittests()
    x = get_logger("foo.bar")
    x = x.bind(k1=1)
    x = x.bind(k2='bar')
    x.warning("foo")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo", "{k1=1 k2=bar}")
    tmp = _test_json("WARNING", "foo")
    assert tmp['k1'] == 1
    assert tmp['k2'] == 'bar'


def test_logging1():
    reset_unittests()
    x = logging.getLogger("foo.bar")
    x.warning("foo%s", "bar")
    assert UNIT_TESTS_STDOUT == []
    _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foobar")
    _test_json("WARNING", "foobar")


def test_logging2():
    reset_unittests()
    x = logging.getLogger()
    x.info("foo")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo")


def test_thread_local_context():
    reset_unittests()
    print("plop")
    set_config(thread_local_context=True)
    print("/plop")
    x = get_logger("foo.bar")
    x = x.bind(k1=1, k2="bar")
    x.info("foo", k1=2, k3=2)
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo", "{k1=2 k2=bar k3=2}")
    reset_unittests()
    y = get_logger("foo.bar2")
    y.info("foo", k1=2, k3=2)
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo", "{k1=2 k2=bar k3=2}")
    print("plip")
    set_config()
    print("/plip")
    reset_unittests()
    z = get_logger()
    z.info("foo", k1=2, k3=2)
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo", "{k1=2 k3=2}")
