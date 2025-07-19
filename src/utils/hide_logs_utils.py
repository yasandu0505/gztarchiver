import logging
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

def hide_logs():
    # Suppress all Scrapy logs
    configure_logging(install_root_handler=False)
    logging.getLogger('scrapy').setLevel(logging.ERROR)

    # Setup crawler
    settings = get_project_settings()
    settings.set('LOG_LEVEL', 'ERROR')
    
    return settings