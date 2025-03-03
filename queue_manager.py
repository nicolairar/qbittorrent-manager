#!/usr/bin/env python3
import time
import os
import sys
from qbittorrent import Client
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Color definitions for logging
DARK_ORANGE = '\033[38;5;172m'  # Darker orange
DARK_ORANGE_PLUS = '\033[38;5;208m'  # Less dark orange
DARK_ORANGE_MAXIMUM = '\033[38;5;166m'  # Very dark orange

ORANGE = '\033[93m'
RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'

# Configure logging to write to both file and stdout
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.getenv('LOG_PATH', '/var/log/qbit_queue_manager.log'))
    ]
)

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# qBittorrent configuration from env
QB_URL = os.getenv('QB_URL', 'http://gluetun:8080')
QB_USERNAME = os.getenv('QB_USERNAME', 'admin')
QB_PASSWORD = os.getenv('QB_PASSWORD', 'password')

# Thresholds from env
MIN_SPEED_KB = int(os.getenv('MIN_SPEED', 800))  # Speed in KB/s
MIN_SPEED = MIN_SPEED_KB * 1024  # Convert to bytes for comparisons
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 180))  # 3 minutes between checks
REQUIRED_SLOW_COUNT = 3  # Number of consecutive slow averages before moving

# Dictionary to store speed history and count for each torrent
torrent_speeds = {}  # Stores last 3 speeds
slow_torrent_counts = {}  # Counts how many times the average was below threshold

# States to consider as "active"
ACTIVE_STATES = {
    'downloading',
    'metaDL',
    'stalledDL',
    'forcedDL',
    'checkingDL',
    'pausedDL',
    'downloading_metadata'
}

# States to exclude
EXCLUDED_STATES = {
    'queued',
    'queuedDL',
    'queuedUP'
}

def connect_qbittorrent():
    """ Connects to qBittorrent and returns the client instance """
    logger.debug(f"Attempting to connect to qBittorrent at {QB_URL}")
    try:
        qb = Client(QB_URL)
        qb.login(QB_USERNAME, QB_PASSWORD)
        logger.info("Successfully connected to qBittorrent")
        return qb
    except Exception as e:
        logger.error(f"Failed to connect to qBittorrent: {str(e)}")
        raise

def move_to_bottom_of_queue(qb, hash):
    """ Moves the specified torrent to the bottom of the queue """
    try:
        qb._post('torrents/bottomPrio', data={'hashes': hash})
        return True
    except Exception as e:
        logger.error(f"Error moving the torrent: {str(e)}")
        return False

def check_and_requeue():
    """ Checks torrents and moves slow ones to the bottom of the queue if necessary """
    try:
        logger.debug("Starting check_and_requeue function")
        qb = connect_qbittorrent()
        torrents = qb.torrents()
        
        logger.debug(f"Found {len(torrents)} total torrents")
        current_time = time.time()
        
        # Filter active torrents (not queued)
        active_torrents = [t for t in torrents if t['state'] in ACTIVE_STATES and t['state'] not in EXCLUDED_STATES]
        logger.debug(f"Found {len(active_torrents)} active torrents")
        
        # Track currently active torrents
        current_hashes = set()
        
        for torrent in active_torrents:
            current_speed = torrent['dlspeed']
            hash = torrent['hash']
            state = torrent['state']
            current_hashes.add(hash)
            current_speed_kb = current_speed / 1024

            # Log speed with color coding
            speed_text = f"{RED}{current_speed_kb:.0f} KB/s{ENDC}" if current_speed_kb < MIN_SPEED_KB else f"{GREEN}{current_speed_kb:.0f} KB/s{ENDC}"
            logger.debug(f"Checking torrent: {torrent['name']} - State: {state} - Current speed: {speed_text}")

            # Store speed history
            if hash not in torrent_speeds:
                torrent_speeds[hash] = []
            torrent_speeds[hash].append(current_speed_kb)

            # Keep only the last 3 speed records (covering 9 minutes)
            if len(torrent_speeds[hash]) > 3:
                torrent_speeds[hash].pop(0)

            # Calculate the average speed over the last 3 records
            avg_speed_kb = sum(torrent_speeds[hash]) / len(torrent_speeds[hash])

            # Reset counter if any speed was above the threshold
            if current_speed_kb >= MIN_SPEED_KB:
                slow_torrent_counts[hash] = 0
                logger.debug(f"{GREEN}Reset slow count for {torrent['name']} due to speed {current_speed_kb:.0f} KB/s{ENDC}")
            else:
                # Increase slow count if the average is still under the limit
                slow_torrent_counts[hash] = slow_torrent_counts.get(hash, 0) + 1

                # Select color based on the number of slow detections
                if slow_torrent_counts[hash] == 1:
                    color = DARK_ORANGE
                elif slow_torrent_counts[hash] == 2:
                    color = DARK_ORANGE_PLUS
                else:
                    color = DARK_ORANGE_MAXIMUM

                logger.debug(f"{color}Torrent {torrent['name']} has had a slow average {slow_torrent_counts[hash]}/{REQUIRED_SLOW_COUNT} times{ENDC}")

                # Move torrent if it has been slow for REQUIRED_SLOW_COUNT consecutive times
                if slow_torrent_counts[hash] >= REQUIRED_SLOW_COUNT:
                    logger.info(f"{RED}Torrent {torrent['name']} has had a low average speed for {REQUIRED_SLOW_COUNT * CHECK_INTERVAL/60:.0f} minutes, moving to bottom of queue{ENDC}")
                    if move_to_bottom_of_queue(qb, hash):
                        logger.info(f"Successfully moved {torrent['name']} to bottom of queue")
                        del slow_torrent_counts[hash]  # Reset tracking

        # Cleanup non-active torrents from tracking
        for hash in list(slow_torrent_counts.keys()):
            if hash not in current_hashes:
                del slow_torrent_counts[hash]

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)

def main():
    """ Main loop to periodically check torrents """
    logger.info("qBittorrent queue management script started")
    logger.info(f"Configuration:")
    logger.info(f"QB_URL: {QB_URL}")
    logger.info(f"Minimum speed threshold: {MIN_SPEED_KB} KB/s")
    logger.info(f"Check interval: {CHECK_INTERVAL/60:.0f} minutes")
    logger.info(f"Slow threshold: {REQUIRED_SLOW_COUNT * CHECK_INTERVAL} seconds")
    logger.info(f"Active states being monitored: {ACTIVE_STATES}")
    logger.info(f"Excluded states: {EXCLUDED_STATES}")
    
    while True:
        try:
            check_and_requeue()
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}", exc_info=True)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

