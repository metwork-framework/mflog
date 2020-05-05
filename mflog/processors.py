# -*- coding: utf-8 -*-

import os
import structlog
from mflog.utils import level_name_to_level_no, get_level_no_from_logger_name
from mflog.utils import get_extra_context


def fltr(logger, method_name, event_dict):
    """Filter log messages."""
    method_level_no = level_name_to_level_no(method_name)
    logger_level_no = \
        get_level_no_from_logger_name(event_dict.get('name', ''))
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


def add_extra_context(logger, method_name, event_dict):
    """Add extra context in the event dict."""
    extra_context = get_extra_context()
    event_dict.update(extra_context)
    return event_dict


def add_exception_info(logger, method_name, event_dict):
    exc_info = event_dict.pop("exc_info", None)
    if exc_info:
        e = structlog.processors._figure_out_exc_info(exc_info)
        if e[0] is not None:
            event_dict["exception"] = structlog._frames._format_exception(e)
            event_dict["exception_type"] = e[0].__name__
            event_dict["exception_file"] = e[-1].tb_frame.f_code.co_filename
            event = event_dict.get("event", "")
            if isinstance(event, Exception):
                # see issue #3
                # => we convert the exception object in string to avoid
                #    json serializing issues
                event_dict["event"] = str(event)
        else:
            event_dict["exception"] = None
        return event_dict
    return event_dict


def kv_renderer(logger, method_name, event_dict):
    ordered_items = sorted(event_dict.items())
    return " ".join(["%s=%s" % (k, v) for k, v in ordered_items])
