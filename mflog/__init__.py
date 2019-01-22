# -*- coding: utf-8 -*-

import os
import sys
import json
import fnmatch
import logging
import structlog

LOGGING_CONFIG_SET = False
MODULE = os.environ.get('MODULE', 'UNKNOWN')
MFCOM_HOME = os.environ.get('MFCOM_HOME', None)
MODULE_HOME = os.environ.get('MODULE_HOME', None)
DEFAULT_LEVEL = os.environ.get('%s_LOG_DEFAULT_LEVEL' % MODULE, 'INFO')
ADMIN_DEFAULT_LEVEL = os.environ.get('%s_LOG_ADMIN_DEFAULT_LEVEL' % MODULE,
                                     'WARNING')
ADMIN_FILE = os.environ.get('%s_LOG_ADMIN_FILE' % MODULE, None)
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


def _level_name_to_level_no(level_name):
    """Convert level_name (debug, WARNING...) to level number.

    Args:
        level_name (string): A level name (debug, warning, info, critical
            or errot), case insensitive.

    Returns:
        (int) Corresponding level number (in logging library).

    Raises:
        Exception: if the level in unknown.

    """
    ulevel_name = level_name.upper()
    if ulevel_name == "DEBUG" or ulevel_name == "NOTSET":
        return logging.DEBUG
    elif ulevel_name == "INFO":
        return logging.INFO
    elif ulevel_name == "WARNING":
        return logging.WARNING
    elif ulevel_name == "ERROR" or ulevel_name == "EXCEPTION":
        return logging.ERROR
    elif ulevel_name == "CRITICAL":
        return logging.CRITICAL
    else:
        raise Exception("unknown level name: %s" % level_name)


DEFAULT_LEVEL_NO = _level_name_to_level_no(DEFAULT_LEVEL)
ADMIN_DEFAULT_LEVEL_NO = _level_name_to_level_no(ADMIN_DEFAULT_LEVEL)
MFCOM_OVERRIDE_LINES_CACHE = None
MODULE_OVERRIDE_LINES_CACHE = None
LEVEL_FROM_LOGGER_NAME_CACHE = {}


def __file_to_lines(file_path):
    """Read the given file_path and decode python_logging_override format.

    foo.bar.* => DEBUG
    foo.* => WARNING

    Notes:
    - lines beginning with # are ignored
    - the left part is a read as a fnmatch pattern
    - the right part is a case insensitive level name

    Args:
        file_path (string): The full path of the file to read.

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    try:
        with open(file_path, "r") as f:
            tmp = [x.split('=>') for x in f.readlines()]
            lines = [(x[0].strip(), x[1].strip()) for x in tmp
                     if len(x) == 2 and not x[0].strip().startswith('#')]
        return lines
    except IOError:
        return []


def _get_mfcom_override_lines():
    """Read the mfcom python_logging_override.conf file (if exists).

    Note: the content is cached (in memory).

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    global MFCOM_OVERRIDE_LINES_CACHE
    if MFCOM_OVERRIDE_LINES_CACHE is None:
        lines = []
        if MFCOM_HOME:
            lines = __file_to_lines("%s/config/python_logging_override.conf" %
                                    MFCOM_HOME)
        MFCOM_OVERRIDE_LINES_CACHE = lines
    return MFCOM_OVERRIDE_LINES_CACHE


def _get_module_override_lines():
    """Read the current module python_logging_override.conf file (if exists).

    Note: the content is cached (in memory).

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    global MODULE_OVERRIDE_LINES_CACHE
    if MODULE_OVERRIDE_LINES_CACHE is None:
        lines = []
        if MODULE_HOME:
            lines = __file_to_lines("%s/config/python_logging_override.conf" %
                                    MODULE_HOME)
        MODULE_OVERRIDE_LINES_CACHE = lines
    return MODULE_OVERRIDE_LINES_CACHE


def __get_level_no_from_logger_name(logger_name):
    """Get the level number to use for the given logger name.

    Note: we check first the current module python_logging_override.conf file
        then the mfcom python_logging_override.conf file then we return
        the default level number. The first match wins.

    Args:
        logger_name (string): The logger name.

    Returns:
        (int) The level number to use for this logger name.

    """
    module_lines = _get_module_override_lines()
    for k, v in module_lines:
        if fnmatch.fnmatch(logger_name, k):
            return _level_name_to_level_no(v)
    mfcom_lines = _get_mfcom_override_lines()
    for k, v in mfcom_lines:
        if fnmatch.fnmatch(logger_name, k):
            return _level_name_to_level_no(v)
    return DEFAULT_LEVEL_NO


def _get_level_no_from_logger_name(logger_name):
    """Get the level number to use for the given logger name.

    Note: we check first the current module python_logging_override.conf file
        then the mfcom python_logging_override.conf file then we return
        the default level number. The first match wins.

    Note: the result is cached in memory.

    Args:
        logger_name (string): The logger name.

    Returns:
        (int) The level number to use for this logger name.

    """
    global LEVEL_FROM_LOGGER_NAME_CACHE
    if logger_name not in LEVEL_FROM_LOGGER_NAME_CACHE:
        LEVEL_FROM_LOGGER_NAME_CACHE[logger_name] = \
            __get_level_no_from_logger_name(logger_name)
    return LEVEL_FROM_LOGGER_NAME_CACHE[logger_name]


def fltr(logger, method_name, event_dict):
    """Filter log messages."""
    method_level_no = _level_name_to_level_no(method_name)
    logger_level_no = \
        _get_level_no_from_logger_name(event_dict.get('name', ''))
    if method_level_no < logger_level_no:
        raise structlog.DropEvent
    return event_dict


def add_level(logger, method_name, event_dict):
    """Add the severity in the event_dict."""
    event_dict['level'] = method_name.lower()
    return event_dict


def add_pid(logger, method_name, event_dict):
    """Add the current pid in the event dict."""
    event_dict['pid'] = os.getpid()
    return event_dict


def add_exception_info(logger, method_name, event_dict):
    exc_info = event_dict.pop("exc_info", None)
    if exc_info:
        e = structlog.processors._figure_out_exc_info(exc_info)
        event_dict["exception"] = structlog._frames._format_exception(e)
        event_dict["exception_type"] = e[0].__name__
        event_dict["exception_file"] = e[-1].tb_frame.f_code.co_filename
        return event_dict
    return event_dict


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
            self.__loggers[name] = structlog.get_logger(name)
        return self.__loggers[name]

    def emit(self, record):
        kwargs = {'name': record.name}
        if record.exc_info:
            kwargs['exc_info'] = record.exc_info
        logger = self.__get_logger(record.name)
        if record.levelno == logging.DEBUG:
            logger.debug(record.msg, **kwargs)
        elif record.levelno == logging.INFO:
            logger.info(record.msg, **kwargs)
        elif record.levelno == logging.WARNING:
            logger.warning(record.msg, **kwargs)
        elif record.levelno == logging.ERROR:
            logger.error(record.msg, **kwargs)
        elif record.levelno == logging.CRITICAL:
            logger.critical(record.msg, **kwargs)
        else:
            raise Exception("unknown levelno: %i" % record.levelno)


class MFLogBoundLogger(structlog.BoundLoggerBase):

    def debug(self, event=None, *args, **kw):
        return self._proxy_to_logger("debug", event, *args, **kw)

    def info(self, event=None, *args, **kw):
        return self._proxy_to_logger("info", event, *args, **kw)

    def warning(self, event=None, *args, **kw):
        return self._proxy_to_logger("warning", event, *args, **kw)

    def critical(self, event=None, *args, **kw):
        return self._proxy_to_logger("critical", event, *args, **kw)

    def error(self, event=None, *args, **kw):
        return self._proxy_to_logger("error", event, *args, **kw)

    def exception(self, event=None, *args, **kw):
        kw.setdefault("exc_info", True)
        return self.error(event, *args, **kw)

    def _proxy_to_logger(self, method_name, event, *event_args, **event_kw):
        """
        Propagate a method call to the wrapped logger.

        This is the same as the superclass implementation, except that
        it also preserves positional arguments in the `event_dict` so
        that the stdblib's support for format strings can be used.
        """
        if event_args:
            event_kw["positional_args"] = event_args
        return super(MFLogBoundLogger, self)._proxy_to_logger(method_name,
                                                              event=event,
                                                              **event_kw)

    warn = warning
    fatal = critical
    msg = info


class MFLogLogger(object):

    _stdout_print_logger = None
    _stderr_print_logger = None
    _admin_file = None
    _unittests_stdout = None
    _unittests_stderr = None
    _unittests_admin = None

    def __init__(self):
        self._stdout_print_logger = structlog.PrintLogger(sys.stdout)
        self._stderr_print_logger = structlog.PrintLogger(sys.stderr)
        if ADMIN_FILE or UNIT_TESTS_MODE:
            if UNIT_TESTS_MODE:
                self._admin_file = open('/dev/null', 'w+')
            else:
                self._admin_file = open(ADMIN_FILE, 'w+')
            self._json_logger = structlog.PrintLogger(self._admin_file)
        if UNIT_TESTS_MODE:
            self._stdout_print_logger._flush = lambda *args, **kwargs: None
            self._stdout_print_logger._write = UNIT_TESTS_STDOUT.append
            self._stderr_print_logger._flush = lambda *args, **kwargs: None
            self._stderr_print_logger._write = UNIT_TESTS_STDERR.append
            self._json_logger._flush = lambda *args, **kwargs: None
            self._json_logger._write = UNIT_TESTS_ADMIN.append

    def _msg_stdout(self, **event_dict):
        self._admin(**event_dict)
        self._stdout_print_logger.msg(self._format(event_dict))

    def _msg_stderr(self, **event_dict):
        self._admin(**event_dict)
        self._stderr_print_logger.msg(self._format(event_dict))

    def _admin(self, **event_dict):
        if ADMIN_FILE is None and not UNIT_TESTS_MODE:
            return
        method_level_no = _level_name_to_level_no(event_dict['level'])
        if method_level_no < ADMIN_DEFAULT_LEVEL_NO:
            return
        self._json_logger.msg(json.dumps(event_dict))

    def _format(self, event_dict):
        level = "[%s]" % event_dict.pop('level').upper()
        ts = event_dict.pop('timestamp')
        name = event_dict.pop('name', 'root')
        pid = event_dict.pop('pid')
        msg = event_dict.pop('event')
        exc = event_dict.pop('exception', None)
        event_dict.pop('exception_type', None)
        event_dict.pop('exception_file', None)
        extra = ""
        if len(event_dict) > 0:
            kvr = structlog.processors.KeyValueRenderer
            extra = " {%s}" % kvr(sort_keys=True)(None, None, event_dict)
        tmp = "%s %10s (%s#%i) %s%s" % (ts, level, name, pid, msg, extra)
        if exc is not None:
            tmp = tmp + "\n" + exc
        return tmp

    def _json_format(self, event_dict):
        return json.dumps(event_dict)

    debug = info = msg = _msg_stdout
    error = critical = warning = exception = _msg_stderr


class MFLogLoggerFactory(object):

    def __call__(self, *args):
        return MFLogLogger()


def set_logging_config():
    """Set the logging configuration.

    The configuration is cached. So you can call this several times.

    """
    global LOGGING_CONFIG_SET
    if LOGGING_CONFIG_SET:
        return
    # Configure standard logging redirect to structlog
    root_logger = logging.getLogger()
    root_logger.addHandler(StructlogHandler())
    root_logger.setLevel(logging.NOTSET)

    # Configure structlog
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
        wrapper_class=MFLogBoundLogger,
        logger_factory=MFLogLoggerFactory()
    )
    LOGGING_CONFIG_SET = True


def getLogger(*args, **kwargs):
    """Return a python logging logger.

    This function is just a wrapper.

    But by importing and using this one (and not directly logging.getLogger
    or structlog.get_logger),
    you are sure that the logging config is set.
    """
    set_logging_config()
    if len(args) == 1:
        return structlog.get_logger(name=args[0], **kwargs)
    else:
        return structlog.get_logger(**kwargs)


def get_logger(*args, **kwargs):
    """Return a python logging logger.

    This function is just a wrapper.

    But by importing and using this one (and not directly logging.getLogger
    or structlog.get_logger),
    you are sure that the logging config is set.
    """
    return getLogger(*args, **kwargs)
