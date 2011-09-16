"""
Common interface for propagating logable messages.
"""
import logging

# Default name for the `global_logger`
DEFAULT_GLOBAL_LOGGER_NAME = 'Launchit'

def get_console_logger(name, format='%(name)s: [%(levelname)s] %(message)s'):
    """
    Return a logger with the given `name`, which is able to write messages to 
    a terminal's `stderr`-stream by using the given `format`. See the `logging`
    module's documentation for details.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter(format)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

# Used by `info()`, `warning()` and `error()` in order to provide a simplified
# way for other modules, when they need to show status messages.
global_logger = get_console_logger(DEFAULT_GLOBAL_LOGGER_NAME)

def info(message):
    """
    Log a message with logging level `INFO` on the `global_logger`.
    """
    global_logger.info(message)

def warning(message):
    """
    Log a message with logging level `WARNING` on the `global_logger`.
    """
    global_logger.warning(message)

def error(message):
    """
    Log a message with logging level `ERROR` on the `global_logger`.
    """
    global_logger.error(message)
