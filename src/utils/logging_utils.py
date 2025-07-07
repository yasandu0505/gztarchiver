"""
Logging Utils Module
Configures Scrapy logging based on configuration and CLI arguments.
"""

import logging
from scrapy.utils.log import configure_logging


def configure_scrapy_logging(config_loader, enable_logs):
    """Configure Scrapy logging based on config and CLI args."""
    scrapy_settings = config_loader.get_scrapy_settings()
    
    if enable_logs.upper() != "Y":
        log_level = scrapy_settings.get('LOG_LEVEL', 'CRITICAL')
        log_format = scrapy_settings.get('LOG_FORMAT', '%(levelname)s: %(message)s')
        log_stdout = scrapy_settings.get('LOG_STDOUT', False)
        
        configure_logging({
            'LOG_LEVEL': log_level,
            'LOG_FORMAT': log_format,
            'LOG_STDOUT': log_stdout
        })
        logging.getLogger('scrapy').propagate = False