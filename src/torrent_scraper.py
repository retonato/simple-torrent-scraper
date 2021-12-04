"""Simple torrent scraper."""
import logging
import os
import sys
import threading
from glob import glob
from logging.handlers import TimedRotatingFileHandler
from signal import SIGINT, SIGTERM, signal

from src import session

if __name__ == "__main__":
    # Generate folders, if necessary
    for folder in ["logs", "results"]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Configure logging
    log_f = os.path.join("logs/log.txt")
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[TimedRotatingFileHandler(log_f, utc=True, when="midnight")],
        level=logging.INFO,
    )

    # Handle close signal gracefully
    stop = threading.Event()
    signal(SIGINT, lambda *args: stop.set())
    signal(SIGTERM, lambda *args: stop.set())

    # Load source info hashes
    with open(sys.argv[1], "r", encoding="utf8") as source_file:
        info_hashes = set()
        for line in source_file:
            if len(line.strip()) == 40:
                info_hashes.add(line.strip())
    logging.info("Source file: %s", sys.argv[1])
    logging.info("%s info hashes loaded", len(info_hashes))

    # Filter out existing torrents
    for filepath in glob("results/**/*.torrent", recursive=True):
        info_hashes.discard(filepath.split("/")[-1].split(".")[0])
    logging.info("%s info hashes remained (-torrents)", len(info_hashes))

    for filepath in sorted(glob("results/**/*.txt", recursive=True)):
        with open(filepath, encoding="utf8") as source_file:
            already_found = set()
            for line in source_file:
                if len(line.strip()) == 40:
                    already_found.add(line.strip())
            info_hashes -= already_found
            logging.info(
                "%s info hashes remained (-%s)", len(info_hashes), filepath
            )

    # Create libtorrent session
    session.start_libtorrent_session(info_hashes, stop)
    logging.info("Source file: %s", sys.argv[1])
    logging.info("Exiting!\n")
