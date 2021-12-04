A simple torrent scraper.

Usage:
- install Python 3.7 (or newer)
- pip install -r requirements.txt
- python -m src.torrent_scraper <path_to_source_file>  # one info hash per line

Scraper starts a torrent client and tries to obtain .torrent files using BEP9. 
Session parameters - 1 thread, up to 500 simultaneous downloads, waiting time 
up to 15 minutes. Don't forget to forward/open port 60300 in your 
router/firewall. No actual files are downloaded.

Obtained .torrent files saved to "results" folder. Logs are saved to "logs" 
folder, one file per day.
