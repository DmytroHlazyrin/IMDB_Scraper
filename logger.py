import logging


def setup_logger(
        name: str, log_file: str, level=logging.INFO
) -> logging.Logger:
    """Function to setup logger with specified name, log file, and level."""

    # Create logger object
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create file handler to log to a file
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    # Format the log messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger
