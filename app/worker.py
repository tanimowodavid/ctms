"""Background worker for durable email delivery."""

import argparse
import logging
import time

from app.core.config import settings
from app.services.email_service import process_next_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def run(*, once: bool = False) -> None:
	while True:
		try:
			processed = process_next_email()
		except Exception:
			logger.exception("Email worker failed while processing the outbox")
			processed = False
		if once:
			return
		if not processed:
			time.sleep(settings.worker_poll_seconds)


def main() -> None:
	parser = argparse.ArgumentParser(prog="ctms-worker")
	parser.add_argument("--once", action="store_true", help="process one due email and exit")
	args = parser.parse_args()
	run(once=args.once)


if __name__ == "__main__":
	main()
