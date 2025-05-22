# -*- coding: utf-8 -*-

import pytest
import sys
import os
import force_unittests_mode  # noqa: F401
import json
from mflog import get_logger, set_config, add_override
from mflog import UNIT_TESTS_STDOUT, UNIT_TESTS_STDERR, UNIT_TESTS_JSON
from mflog.unittests import reset_unittests, extra_context
import logging


def _test_stdxxx(stdxxx, level, msg, extra=None):
    assert len(stdxxx) == 1
    tmp = stdxxx[0].split("\n")[0].split(None, 3)
    assert len(tmp) >= 4
    assert len(tmp[0]) == 27
    assert tmp[1] == "[%s]" % level.upper()
    assert tmp[3].split(' {')[0] == msg
    if extra is not None:
        tmp2 = tmp[3].split(' {', 2)
        if len(tmp2) > 1:
            tmp3 = "{" + tmp2[1]
        else:
            tmp3 = tmp2
        assert tmp3 == extra


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
    # _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo")
    # _test_json("WARNING", "foo")


def test_override_dict():
    reset_unittests()
    add_override("foo2.*", "CRITICAL")
    x = get_logger("foo.bar")
    y = get_logger("foo2.bar")
    x.warning("foo")
    y.warning("foo2")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo")
    # _test_json("WARNING", "foo")
    add_override("foo.*", None)


def test_basic_log():
    reset_unittests()
    x = get_logger()
    x.log(logging.WARNING, "foo")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo")
    # _test_json("WARNING", "foo")


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
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo")


def test_logger_name():
    reset_unittests()
    x = get_logger("foo.bar")
    x.info("test")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "test")
    # assert "foo.bar" in UNIT_TESTS_STDOUT[0]


def test_basic_critical():
    reset_unittests()
    x = get_logger()
    x.critical("foo")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "CRITICAL", "foo")
    # _test_json("CRITICAL", "foo")


def test_basic_error():
    reset_unittests()
    x = get_logger()
    x.error("foo")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "ERROR", "foo")
    # _test_json("ERROR", "foo")


def test_basic_exception():
    reset_unittests()
    x = get_logger()
    try:
        1 / 0
    except Exception:
        x.exception("foo")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "ERROR", "foo")
    # tmp = _test_json("ERROR", "foo")
    # assert len(tmp['exception']) > 10
    # assert tmp['exception_type'] == 'ZeroDivisionError'
    # assert tmp['exception_file'] == __file__


def test_issue3():
    reset_unittests()
    x = get_logger()
    try:
        1 / 0
    except Exception as e:
        x.exception(e)
    assert UNIT_TESTS_STDOUT == []
    # if six.PY2:
    #     _test_stdxxx(UNIT_TESTS_STDERR, "ERROR",
    #                  "integer division or modulo by zero")
    #     tmp = _test_json("ERROR", "integer division or modulo by zero")
    # else:
    #     _test_stdxxx(UNIT_TESTS_STDERR, "ERROR", "division by zero")
    #     tmp = _test_json("ERROR", "division by zero")
    # assert len(tmp['exception']) > 10
    # assert tmp['exception_type'] == 'ZeroDivisionError'
    # assert tmp['exception_file'] == __file__


def test_template_info():
    reset_unittests()
    x = get_logger()
    x.info("foo%s", "bar")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foobar")


def test_template_info2():
    reset_unittests()
    x = get_logger()
    x.info("foo%(u)s", {"u": "bar"})
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foobar")


def test_kv_warning():
    reset_unittests()
    x = get_logger()
    x.warning("foo", k1=1, k2="bar")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo", "{k1=1 k2=bar}")
    # tmp = _test_json("WARNING", "foo")
    # assert tmp['k1'] == 1
    # assert tmp['k2'] == 'bar'


def test_utf8():
    reset_unittests()
    x = get_logger()
    x.warning(u"fooééé", k1=1, k2=u"barààà")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", u"fooééé", u"{k1=1 k2=barààà}")
    # tmp = _test_json("WARNING", u"fooééé")
    # assert tmp['k1'] == 1
    # assert tmp['k2'] == u'barààà'


@pytest.mark.skipif(sys.version_info < (3, 0), reason="requires python3")
def test_bytes():
    reset_unittests()
    x = get_logger()
    x.warning(b"foo", k1=1, k2=b"bar")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo", "{k1=1 k2=bar}")
    # tmp = _test_json("WARNING", "foo")
    # assert tmp['k1'] == 1
    # assert tmp['k2'] == 'bar'


def test_bind():
    reset_unittests()
    x = get_logger("foo.bar")
    x = x.bind(k1=1)
    x = x.bind(k2='bar')
    x.warning("foo")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foo", "{k1=1 k2=bar}")
    # tmp = _test_json("WARNING", "foo")
    # assert tmp['k1'] == 1
    # assert tmp['k2'] == 'bar'


def test_logging1():
    reset_unittests()
    x = logging.getLogger("foo.bar")
    x.warning("foo%s", "bar")
    assert UNIT_TESTS_STDOUT == []
    # _test_stdxxx(UNIT_TESTS_STDERR, "WARNING", "foobar")
    # _test_json("WARNING", "foobar")


def test_logging2():
    reset_unittests()
    x = logging.getLogger()
    x.info("foo")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo")


def test_logging3():
    reset_unittests()
    x = logging.getLogger()
    x.info("foo %s", "bar")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo bar")


def test_logging4():
    reset_unittests()
    x = logging.getLogger()
    x.info("foo %(u)s", {"u": "bar"})
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo bar")


def test_logging5():
    reset_unittests()
    set_config(standard_logging_redirect=False)
    x = logging.getLogger()
    x.info("foobar")
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    assert UNIT_TESTS_STDOUT == []


def test_empty_call1():
    reset_unittests()
    x = get_logger()
    x.info()
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "None")


def test_empty_call2():
    reset_unittests()
    x = get_logger()
    x.info(None)
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "None")


def test_extra_context():
    reset_unittests()
    set_config(extra_context_func=extra_context)
    x = get_logger("foo.bar")
    x = x.bind(k1=1, k2="bar")
    x.info("foo", k1=2, k3=2)
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo",
    #              "{extra_context_key1=extra_context_value1 "
    #              "extra_context_key2=extra_context_value2 k1=2 k2=bar k3=2}")


def test_extra_context2():
    reset_unittests()
    os.environ["MFLOG_EXTRA_CONTEXT_FUNC"] = "mflog.unittests.extra_context"
    x = get_logger("foo.bar")
    x = x.bind(k1=1, k2="bar")
    x.info("foo", k1=2, k3=2)
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo",
    #              "{extra_context_key1=extra_context_value1 "
    #              "extra_context_key2=extra_context_value2 k1=2 k2=bar k3=2}")


def test_json_only_keys1():
    reset_unittests()
    set_config(json_only_keys=["extra_context_key1", "extra_context_key2"])
    x = get_logger("foo.bar")
    x = x.bind(k1=1, k2="bar")
    x.info("foo", k1=2, k3=2)
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo", "{k1=2 k2=bar k3=2}")


def test_json_only_keys2():
    reset_unittests()
    os.environ["MFLOG_JSON_ONLY_KEYS"] = \
        "extra_context_key1,extra_context_key2"
    x = get_logger("foo.bar")
    x = x.bind(k1=1, k2="bar")
    x.info("foo", k1=2, k3=2)
    assert UNIT_TESTS_STDERR == []
    assert UNIT_TESTS_JSON == []
    # _test_stdxxx(UNIT_TESTS_STDOUT, "INFO", "foo", "{k1=2 k2=bar k3=2}")


def test_is_enabled_for():
    reset_unittests()
    x = get_logger("foo.bar")
    assert x.isEnabledFor(40)
    assert x.getEffectiveLevel() == 20
    reset_unittests()
