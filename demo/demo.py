import mflog

# Get a logger
logger = mflog.get_logger("foobar")

# Bind two context variables to this logger
logger = logger.bind(user_id=1234, is_logged=True)

# Log something
logger.info("This is an info message", special_value="foo")
logger.critical("This is a very interesting critical message")

# Let's play with exception
try:
    # Just set a variable to get a demo of locals variable dump
    var = {"key1": [1, 2, 3], "key2": "foobar"}
    1/0
except Exception:
    logger.exception("exception raised (a variables dump should follow)")
