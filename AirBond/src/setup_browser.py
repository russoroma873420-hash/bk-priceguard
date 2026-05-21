"""One-time Playwright Chromium installer.

Run this once after `pip install -r requirements.txt`:
    python -m src.setup_browser

It downloads the Chromium build (~150 MB) into the Playwright cache so the
playwright_scraper module can launch it headless. Safe to re-run — Playwright
skips download if the browser is already present.
"""

import logging
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def install_chromium() -> int:
    """Run `playwright install chromium` via subprocess.

    Returns:
        Process exit code (0 = success).
    """
    cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            logger.info("Chromium installed successfully.")
        else:
            logger.error(f"playwright install exited with code {result.returncode}")
        return result.returncode

    except FileNotFoundError:
        logger.error(
            "Could not find Python/Playwright. "
            "Did you run 'pip install -r requirements.txt'?"
        )
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(install_chromium())
