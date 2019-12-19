# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import json
import os
import logging
import logging.config
import structlog
import functools

from mflog.utils import level_name_to_level_no, Config, \
    get_level_no_from_logger_name, write_with_lock, flush_with_lock, \
    __reset_level_from_logger_name_cache
from mflog.processors import fltr, add_level, add_pid, add_exception_info, \
    kv_renderer, add_extra_context
from mflog.unittests import UNIT_TESTS_STDOUT, UNIT_TESTS_STDERR, \
    UNIT_TESTS_JSON, UNIT_TESTS_MODE
from mflog.syslog import SyslogLogger

CONFIGURATION_SET = False


class StructlogHandler(logging.Handler):
    """Feed all events back into `structlog`.

    See https://github.com/hynek/structlog/issues/9
    """

    level = logging.DEBUG
    filters = []
    lock = None
    __loggers = None

    def __init__(self, *args, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        self.__loggers = {}

    def __get_logger(self, name):
        if name not in self.__loggers:
            self.__loggers[name] = get_logger(name)
        return self.__loggers[name]

    def emit(self, record):
        kwargs = {'name': record.name}
        if record.exc_info:
            kwargs['exc_info'] = record.exc_info
        logger = self.__get_logger(record.name)
        if record.levelno >= logging.CRITICAL:
            f = logger.critical
        elif record.levelno >= logging.ERROR:
            f = logger.error
        elif record.levelno >= logging.WARNING:
            f = logger.warning
        elif record.levelno >= logging.INFO:
            f = logger.info
        elif record.levelno >= logging.DEBUG:
            f = logger.debug
        else:
            # let's ignore this
            return
        # Mimick the formatting behaviour of the stdlib's logging
        # module, which accepts both positional arguments and a single
        # dict argument.
        if record.args and isinstance(record.args, dict):
            f(record.msg, record.args, **kwargs)
        else:
            f(record.msg, *(record.args), **kwargs)


class MFLogLogger(object):

    _stdout_print_logger = None
    _stderr_print_logger = None
    _syslog_logger = None
    _json_file = None
    _unittests_stdout = None
    _unittests_stderr = None
    _unittests_json = None
    _json_only_keys = None
    name = None

    def __init__(self, *args):
        if len(args) > 0:
            self.name = args[0]
        else:
            self.name = 'root'
        self._stdout_print_logger = structlog.PrintLogger(sys.stdout)
        self._stderr_print_logger = structlog.PrintLogger(sys.stderr)
        if Config.syslog_address:
            self._syslog_logger = SyslogLogger(Config.syslog_address,
                                               Config.syslog_format)
        if Config.json_file or UNIT_TESTS_MODE:
            if UNIT_TESTS_MODE or Config.json_file is None:
                self._json_file = open('/dev/null', 'a')
                self._json_logger = structlog.PrintLogger(self._json_file)
            else:
                self._json_file = open(Config.json_file, 'a')
                self._json_logger = structlog.PrintLogger(self._json_file)
                self._json_logger._write = functools.partial(write_with_lock,
                                                             self._json_file)
                self._json_logger._flush = functools.partial(flush_with_lock,
                                                             self._json_file)
        if UNIT_TESTS_MODE:
            self._stdout_print_logger._flush = lambda *args, **kwargs: None
            self._stdout_print_logger._write = UNIT_TESTS_STDOUT.append
            self._stderr_print_logger._flush = lambda *args, **kwargs: None
            self._stderr_print_logger._write = UNIT_TESTS_STDERR.append
            self._json_logger._flush = lambda *args, **kwargs: None
            self._json_logger._write = UNIT_TESTS_JSON.append
        self._json_only_keys = Config.json_only_keys

    def close(self):
        if self._json_file:
            try:
                self._json_file.close()
            except Exception:
                pass
        if self._syslog_logger is not None:
            self._syslog_logger.close()

    def __del__(self):
        self.close()

    def _msg(self, std_logger, **event_dict):
        try:
            self._json(**event_dict)
        except Exception as e:
            print("MFLOG ERROR: can't write log message to json output "
                  "with exception: %s" % e, file=sys.stderr)
        try:
            self._syslog(**event_dict)
        except Exception as e:
            print("MFLOG ERROR: can't write log message to syslog output "
                  "with exception: %s" % e, file=sys.stderr)
        try:
            std_logger.msg(self._format(event_dict))
        except Exception as e:
            print("MFLOG ERROR: can't write log message to stdout/err "
                  "with exception: %s" % e, file=sys.stderr)

    def _msg_stdout(self, **event_dict):
        self._msg(self._stdout_print_logger, **event_dict)

    def _msg_stderr(self, **event_dict):
        self._msg(self._stderr_print_logger, **event_dict)

    def _json(self, **event_dict):
        if Config.json_file is None and not UNIT_TESTS_MODE:
            return
        method_level_no = level_name_to_level_no(event_dict['level'])
        if method_level_no < level_name_to_level_no(Config.json_minimal_level):
            return
        self._json_logger.msg(json.dumps(event_dict))

    def _syslog(self, **event_dict):
        if Config.syslog_address is None:
            return
        method_level_no = level_name_to_level_no(event_dict['level'])
        syslog_minimal_level = Config.syslog_minimal_level
        if method_level_no < level_name_to_level_no(syslog_minimal_level):
            return
        self._syslog_logger.msg(event_dict)

    def _format(self, event_dict):
        level = "[%s]" % event_dict.pop('level').upper()
        ts = event_dict.pop('timestamp')
        name = event_dict.pop('name', 'root')
        pid = event_dict.pop('pid')
        try:
            msg = event_dict.pop('event')
        except KeyError:
            msg = "None"
        exc = event_dict.pop('exception', None)
        event_dict.pop('exception_type', None)
        event_dict.pop('exception_file', None)
        for key in self._json_only_keys:  # pylint: disable=E1133
            try:
                event_dict.pop(key)
            except KeyError:
                pass
        extra = ""
        if len(event_dict) > 0:
            extra = " {%s}" % kv_renderer(None, None, event_dict)
        tmp = "%s %10s (%s#%i) %s%s" % (ts, level, name, pid, msg, extra)
        if exc is not None:
            tmp = tmp + "\n" + exc
        return tmp

    def _json_format(self, event_dict):
        return json.dumps(event_dict)

    def isEnabledFor(self, level):
        logger_level_no = \
            get_level_no_from_logger_name(self.name)
        return level >= logger_level_no

    def getEffectiveLevel(self):
        return get_level_no_from_logger_name(self.name)

    def setLevel(self, level):
        pass

    debug = info = msg = _msg_stdout
    error = critical = warning = exception = _msg_stderr


class MFLogLoggerFactory(object):

    def __call__(self, *args):
        return MFLogLogger(*args)


def set_config(minimal_level=None, json_minimal_level=None,
               json_file=None, override_files=None,
               thread_local_context=False, extra_context_func=None,
               json_only_keys=None, standard_logging_redirect=None,
               override_dict={}, syslog_address=None, syslog_format=None):
    """Set the logging configuration.

    The configuration is cached. So you can call this several times.

    """
    global CONFIGURATION_SET
    Config.set_instance(minimal_level=minimal_level,
                        json_minimal_level=json_minimal_level,
                        json_file=json_file,
                        override_files=override_files,
                        thread_local_context=thread_local_context,
                        extra_context_func=extra_context_func,
                        json_only_keys=json_only_keys,
                        override_dict=override_dict,
                        syslog_address=syslog_address,
                        syslog_format=syslog_format)
    if standard_logging_redirect is not None:
        slr = standard_logging_redirect
    else:
        if 'MFLOG_STANDARD_LOGGING_REDIRECT' in os.environ:
            slr = (os.environ['MFLOG_STANDARD_LOGGING_REDIRECT'] == '1')
        else:
            slr = True  # default value
    if slr:
        # Configure standard logging redirect to structlog
        d = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {},
            "handlers": {},
            "filters": {},
            "loggers": {
                "": {
                    "level": "NOTSET"
                }
            }
        }
        logging.config.dictConfig(d)
        root_logger = logging.getLogger()
        root_logger.addHandler(StructlogHandler())
        root_logger.setLevel(logging.NOTSET)
    else:
        root_logger = logging.getLogger()
        root_logger.handlers = [x for x in root_logger.handlers
                                if not isinstance(x, StructlogHandler)]
    # Configure structlog
    context_class = None
    if thread_local_context:
        context_class = structlog.threadlocal.wrap_dict(dict)
    structlog.reset_defaults()
    structlog.configure(
        processors=[
            fltr,
            add_level,
            add_pid,
            add_extra_context,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            add_exception_info,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.UnicodeDecoder(),
            # See https://stackoverflow.com/a/51629142
            # we do the formatting in the Logger
            lambda _, __, ed: ed
        ],
        cache_logger_on_first_use=True,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=context_class,
        logger_factory=MFLogLoggerFactory()
    )
    CONFIGURATION_SET = True


def add_override(logger_name_pattern, minimal_level_name):
    """Add an override to the configuration.

    You provide a fnmatch pattern to the logger_name as the first argument.
    And the minimal_level_name (WARNING, DEBUG...) to force for this pattern.

    Note: if you use None as minimal_level_name, it will delete the override.

    """
    if not CONFIGURATION_SET:
        set_config()
    if minimal_level_name is None:
        try:
            del(Config.override_dict[logger_name_pattern])
        except KeyError:
            pass
    else:
        # just to raise an exception here
        # if the minimal_level_name is incorrect
        level_name_to_level_no(minimal_level_name)
        d = Config.override_dict
        d[logger_name_pattern] = minimal_level_name
    __reset_level_from_logger_name_cache()


def getLogger(logger_name='root'):
    """Return a python logging logger.

    This function is just a wrapper.

    But by importing and using this one (and not directly logging.getLogger
    or structlog.get_logger),
    you are sure that the logging config is set.
    """
    if not CONFIGURATION_SET:
        set_config()
    return structlog.get_logger(logger_name, name=logger_name)


def get_logger(logger_name='root'):
    """Return a python logging logger.

    This function is just a wrapper.

    But by importing and using this one (and not directly logging.getLogger
    or structlog.get_logger),
    you are sure that the logging config is set.
    """
    return getLogger(logger_name)


def __unset_configuration():
    global CONFIGURATION_SET
    CONFIGURATION_SET = False
