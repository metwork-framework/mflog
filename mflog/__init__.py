# -*- coding: utf-8 -*-

import sys
import json
import logging
import logging.config
import structlog
import functools

from mflog.utils import level_name_to_level_no, Config, \
    get_level_no_from_logger_name, write_with_lock, flush_with_lock
from mflog.processors import fltr, add_level, add_pid, add_exception_info, \
    kv_renderer
from mflog.unittests import UNIT_TESTS_STDOUT, UNIT_TESTS_STDERR, \
    UNIT_TESTS_JSON, UNIT_TESTS_MODE

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
        if record.levelno == logging.DEBUG:
            logger.debug(record.msg, *(record.args), **kwargs)
        elif record.levelno == logging.INFO:
            logger.info(record.msg, *(record.args), **kwargs)
        elif record.levelno == logging.WARNING:
            logger.warning(record.msg, *(record.args), **kwargs)
        elif record.levelno == logging.ERROR:
            logger.error(record.msg, *(record.args), **kwargs)
        elif record.levelno == logging.CRITICAL:
            logger.critical(record.msg, *(record.args), **kwargs)
        else:
            raise Exception("unknown levelno: %i" % record.levelno)


class MFLogLogger(object):

    _stdout_print_logger = None
    _stderr_print_logger = None
    _json_file = None
    _unittests_stdout = None
    _unittests_stderr = None
    _unittests_json = None
    name = None

    def __init__(self, *args):
        if len(args) > 0:
            self.name = args[0]
        else:
            self.name = 'root'
        self._stdout_print_logger = structlog.PrintLogger(sys.stdout)
        self._stderr_print_logger = structlog.PrintLogger(sys.stderr)
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

    def _msg_stdout(self, **event_dict):
        self._json(**event_dict)
        self._stdout_print_logger.msg(self._format(event_dict))

    def _msg_stderr(self, **event_dict):
        self._json(**event_dict)
        self._stderr_print_logger.msg(self._format(event_dict))

    def _json(self, **event_dict):
        if Config.json_file is None and not UNIT_TESTS_MODE:
            return
        method_level_no = level_name_to_level_no(event_dict['level'])
        if method_level_no < level_name_to_level_no(Config.json_minimal_level):
            return
        self._json_logger.msg(json.dumps(event_dict))

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
               thread_local_context=False):
    """Set the logging configuration.

    The configuration is cached. So you can call this several times.

    """
    global CONFIGURATION_SET
    Config.set_instance(minimal_level=minimal_level,
                        json_minimal_level=json_minimal_level,
                        json_file=json_file,
                        override_files=override_files,
                        thread_local_context=thread_local_context)
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
