import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(log_directory='D:\\test\\', log_file='arbitrage_log.log'):
    """
    Sets up a logger with the specified log directory and log file.
    
    Args:
        log_directory (str): The directory where the log file will be stored. Defaults to 'D:\\test\\'.
        log_file (str): The name of the log file. Defaults to 'arbitrage_log.log'.
        
    Returns:
        logger: The logger object that has been set up.
    """
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')
    log_path = os.path.join(log_directory, log_file)
    
    log_handler = RotatingFileHandler(
        log_path,
        mode='a',
        maxBytes=5*1024*1024,
        backupCount=2,
        encoding=None,
        delay=0
    )
    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(logging.INFO)

    logger = logging.getLogger('arbitrage_logger')
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    return logger
