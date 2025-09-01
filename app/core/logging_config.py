import logging
import logging.handlers
import socket

def setup_logging(log_file="jukebox.log", level=logging.DEBUG):
    """Configure logging for the jukebox app."""

    logger = logging.getLogger()
    logger.setLevel(level)

    syslog_address = ('192.168.68.102', 514)  # (IP, port)
    syslog_handler = logging.handlers.SysLogHandler(address=syslog_address)

    hostname = socket.gethostname()
    formatter = logging.Formatter(f'{hostname} %(name)s: %(levelname)s %(message)s')
    syslog_handler.setFormatter(formatter)
    logging.getLogger().addHandler(syslog_handler)

    screen_handler = logging.StreamHandler()
    screen_handler.setFormatter(formatter)
    logging.getLogger().addHandler(screen_handler)
    
    # Suppress noisy logs from third-party libraries
    for lib in ["requests", "PIL", "urllib3", "websockets"]:
        logging.getLogger(lib).setLevel(logging.WARNING)



