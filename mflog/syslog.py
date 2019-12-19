from logging.handlers import SysLogHandler
from logging import LogRecord
import json


class SyslogLoggerMsgOnlyFormatter(object):

    def format(self, record):
        return record.msg['event']


class SyslogLoggerJSONFormatter(object):

    def format(self, record):
        return json.dumps(record.msg)


class SyslogLogger(object):

    __syslog_handler = None

    def __init__(self, address, frmt=None):
        self.__syslog_handler = SysLogHandler(address)
        if frmt is None or frmt == "msg_only":
            self.__syslog_handler.formatter = SyslogLoggerMsgOnlyFormatter()
        else:
            self.__syslog_handler.formatter = SyslogLoggerJSONFormatter()

    def close(self):
        self.__syslog_handler.close()

    def msg(self, event_dict):
        record = LogRecord(event_dict.get("name", "unknown"),
                           event_dict.get("level", "WARNING"),
                           "/not_used/not_used.py", 1,
                           event_dict, [], None)
        self.__syslog_handler.acquire()
        try:
            self.__syslog_handler.emit(record)
        finally:
            self.__syslog_handler.release()
