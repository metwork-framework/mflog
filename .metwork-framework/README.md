## What is it ?

It is an opinionated python (structured) logging library built on [structlog](https://www.structlog.org/)
for the [MetWork Framework](http://metwork-framework.org) (but it can be used in any context).

> Structured logging means that you don’t write hard-to-parse and hard-to-keep-consistent prose in your logs but that you log events that happen in a context instead.
> - https://www.structlog.org/en/stable/why.html

Example:

```python

from mflog import get_logger

# Get a logger
log = get_logger("foo.bar")

# Bind some attributes to the logger depending on the context
log = log.bind(user="john")
log = log.bind(user_id=123)

# [...]

# Log something
log.warning("user logged in", happy=True, another_key=42)
```

On `stderr`, you will get:

```
2019-01-28T07:52:42.903067Z  [WARNING] (foo.bar#7343) user logged in {another_key=42 happy=True user=john user_id=123}
```

On `json output file`, you will get:

```json
{
    "timestamp": "2019-01-28T08:16:40.047710Z",
    "level": "warning",
    "name": "foo.bar",
    "pid": 29317,
    "event": "user logged in",
    "another_key": 42,
    "happy": true,
    "user": "john",
    "user_id": 123
}
```

## (opinionated) Choices

- we use main ideas from `structlog` library
- we log `[DEBUG]` and `[INFO]` messages on `stdout` (in a human friendly way)
- we log `[WARNING]`, `[ERROR]` and `[CRITICAL]` on `stderr` (in a human friendly way)
- (and) we log all messages (worse than a minimal configurable level) in a configurable file in `JSON` (for easy automatic parsing)
- we can configure a global minimal level to ignore all messages below
- we reconfigure automatically python standard logging library to use `mflog`
- UTF-8 messages are ok
- good support for exceptions (with backtrace)

## How to use ?

A `mflog` logger can be used as a standard `logging` logger.

For example:

```python
# Import
from mflog import get_logger

# Get a logger
x = get_logger("foo.bar")

# Usage
x.warning("basic message")
x.critical("message with templates: %i, %s", 2, "foo")
x.debug("message with key/values", foo=True, bar="string")

try:
    1/0
except Exception:
    x.exception("we catched an exception with automatic traceback")

x = log.bind(context1="foo")
x = log.bind(context2="bar")
x.info("this is a contexted message", extra_var=123)
```

## How to configure ?

### In python

```python
import mflog

# Configure
mflog.set_logging_config(minimal_level="DEBUG", json_minimal_level="WARNING",
                         json_file="/foo/bar/my_output.json")

# Get a logger
x = mflog.get_logger("foo.bar")

# [...]
```

### With environment variables

```bash

$ export MFLOG_MINIMAL_LEVEL="DEBUG"
$ export MFLOG_JSON_MINIMAL_LEVEL="WARNING"
$ export MFLOG_JSON_FILE="/foo/bar/my_output.json"

$ python

>>> import mflog
>>>
>>> # Get a logger
>>> x = mflog.get_logger("foo.bar")
>>>
>>> # [...]
```

### In a MetWork module

In a MetWork module, if `MFLOG_MINIMAL_LEVEL`, `MFLOG_JSON_MINIMAL_LEVEL` and
`MFLOG_JSON_FILE` does not exist, there is a failback on:

- ```{MODULE}_LOG_MINIMAL_LEVEL```
- ```{MODULE}_LOG_JSON_MINIMAL_LEVEL```
- ```{MODULE}_LOG_JSON_FILE```

For example, `MFSERV_LOG_MINIMAL_LEVEL` force the minimal level inside the
`MFSERV` module. This particular env var is defined through the standard metwork
configuration.

### Note

When you get a `mflog` logger, if default configuration is applied automatically
if not set manually before.

## How to override minimal level for a specific logger

If you have a "noisy" specific logger, you can override its minimal log level.

The idea is to configure this in a file like this:

```
# lines beginning with # are comments

# this line say 'foo.bar' logger will have a minimal level of WARNING
foo.bar => WARNING

# this line say 'foo.*' loggers will have a minimal level of DEBUG
# (see python fnmatch for accepted wildcards)
foo.* => DEBUG

# The first match wins
```

Then, you can use

```python

# yes we use a list here because you can use several files
# (the first match wins)
mflog.configure([...], override_files=["/full/path/to/your/override.conf"])
```

or

```
# if you want to provide multiple files, use ';' as a separator
export MFLOG_MINIMAL_LEVEL_OVERRIDE_FILES=/full/path/to/your/override.conf
```

In a MetWork context, this is already configured and you can use:

- `{MODULE_RUNTIME_HOME}/config/mflog_override.conf`
- `{MODULE_HOME}/config/mflog_override.conf`
- `{MODULE_HOME}/config/mfcom_override.conf`

## Link with standard python logging library

When you get a `mflog` logger or when you call `set_logging_config()` function,
the standard python `logging` library is reconfigured to use `mflog`.

Example:

```python
import logging
import mflog

# standard use of logging library
x = logging.getLogger("standard.logger")
print("<output of the standard logging library>")
x.warning("foo bar")
print("</output of the standard logging library>")

# we set the mflog configuration
mflog.set_logging_config()

# now logging library use mflog
print()
print("<output of the standard logging library through mflog>")
x.warning("foo bar")
print("</output of the standard logging library through mflog>")
```

Output:

```
<output of the standard logging library>
foo bar
</output of the standard logging library>

<output of the standard logging library through mflog>
2019-01-29T09:32:37.093240Z  [WARNING] (standard.logger#15809) foo bar
</output of the standard logging library through mflog>
```

## Use UTF8 and bytes strings

FIXME

## Use inside libraries

FIXME

## mflog loggers API

FIXME

## Thread Local Context mode

FIXME
