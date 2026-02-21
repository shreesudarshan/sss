"""Application package bootstrap.

This module loads environment variables early and configures shared logging.
Other modules import `logger` from here so we have one consistent logger setup.
"""

import logging

from dotenv import load_dotenv

# Support both common .env naming and existing .ENV in this repo.
load_dotenv(".env")
load_dotenv(".ENV")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("secure-bloom-sse")
