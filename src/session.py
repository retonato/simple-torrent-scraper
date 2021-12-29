"""Code for starting libtorrent session"""
# pylint: disable=c-extension-no-member
import logging
import pathlib
from datetime import date, datetime, timedelta

import libtorrent

from src.settings import settings


def start_libtorrent_session(info_hashes, stop):
    """Start libtorrent session"""
    counters = {"p_ok": [0, 0], "p_nok": [0, 0], "added": [0, 0]}

    # Load trackers and session config
    with open("trackers.txt", encoding="utf8") as source_file:
        trackers = [line.strip() for line in source_file.readlines()]

    # Start libtorrent session
    lt_session = libtorrent.session(settings)
    lt_session.add_extension("metadata_transfer")
    lt_session.add_extension("ut_metadata")
    lt_session.add_extension("ut_pex")

    while not stop.is_set():
        # Check if some of active torrents have metadata
        for torrent in lt_session.get_torrents():
            sha1 = torrent.info_hash().to_bytes().hex()
            t_added = datetime.fromtimestamp(torrent.status().added_time)
            t_age = datetime.now() - t_added

            if torrent.has_metadata():
                # Save obtained metadata
                filepath = pathlib.Path(
                    "results",
                    str(date.today())[:7],
                    sha1[:2],
                    sha1[2:4],
                    f"{sha1}.torrent",
                )
                filepath.parent.mkdir(parents=True, exist_ok=True)
                try:
                    filepath.write_bytes(
                        libtorrent.bencode(
                            libtorrent.create_torrent(
                                torrent.get_torrent_info()
                            ).generate()
                        )
                    )
                except Exception as err:  # pylint: disable=broad-except
                    logging.error(
                        "Cannot save torrent %s, error: %s", sha1, err
                    )

                # Remove the torrent with files (if there are any)
                lt_session.remove_torrent(torrent, lt_session.delete_files)
                counters["p_ok"][0] += 1
                counters["p_ok"][1] += 1

            elif t_age > timedelta(seconds=60 * 15):
                # Remove the torrent with files (if there are any)
                lt_session.remove_torrent(torrent, lt_session.delete_files)
                counters["p_nok"][0] += 1
                counters["p_nok"][1] += 1

        # Add new torrents to the session
        for _ in range(500 - len(lt_session.get_torrents())):
            if info_hashes:
                sha1 = info_hashes.pop()
            else:
                break
            try:
                lt_session.add_torrent(
                    {
                        "file_priorities": [0] * 10000,
                        "info_hashes": bytes.fromhex(sha1),
                        "save_path": "/tmp",
                        "trackers": trackers,
                    }
                )
                counters["added"][0] += 1
                counters["added"][1] += 1
            except Exception as err:  # pylint: disable=broad-except
                logging.error("Cannot add torrent %s, error: %s", sha1, err)
                continue

        if not lt_session.get_torrents():
            stop.set()

        # Log the progress, reset cycle counters
        logging.info(
            "%s processed ok, %s processed nok, %s added, %s remained",
            counters["p_ok"][0],
            counters["p_nok"][0],
            counters["added"][0],
            len(info_hashes),
        )
        for counter in counters:
            counters[counter][0] = 0

        # Wait until the next check
        stop.wait(60)

    logging.info(
        "Total: %s processed ok, %s processed nok, %s added",
        counters["p_ok"][1],
        counters["p_nok"][1],
        counters["added"][1],
    )
