import os
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(env: str = "development", log_level: str = "INFO", db_echo: bool = False) -> None:
    """
    Configure system-wide logging with console and rotating file options.
    Adjusts levels and targets based on active environment (dev, prod, test).
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Production-ready logging format
    log_format = "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Production rotating file logger setup
    if env == "production":
        log_dir = "logs"
        try:
            os.makedirs(log_dir, exist_ok=True)
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, "app.log"),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8"
            )
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        except Exception as e:
            print(f"Failed to initialize rotating file logger: {e}", file=sys.stderr)
        
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers,
        force=True
    )
    
    # Control log levels for standard FastAPI/Uvicorn servers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # Control SQLAlchemy engine SQL query logging
    if db_echo:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        
    logging.info(f"Central logging initialized. Level: {log_level} | Env: {env} | DB Echo: {db_echo}")
