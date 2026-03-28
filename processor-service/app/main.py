import asyncio
import logging

from app.config import get_settings
from app.consumer import run_consumer

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    asyncio.run(run_consumer())
