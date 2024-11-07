import configparser
import logging
import os
import sys

import garminconnect
import garth

from karoo import Karoo

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', )
logger = logging.getLogger(__name__)


def write_configfile(filename):
    text = r"""
[GARMIN]
GARMIN_USERNAME = your_email_address
GARMIN_PASSWORD = your_password

[HAMMERHEAD]
HAMMERHEAD_USERNAME = your_email_address
HAMMERHEAD_PASSWORD = your_password
"""
    with open(filename, 'w') as configfile:
        configfile.write(text)
    print(f'Created {filename}. Add your user details to that file and run karoosync again.')
    sys.exit(0)


def main():
    # Read config file
    CONFIGFILE = 'karoosync.cfg'
    config = configparser.ConfigParser(interpolation=None)

    config_exists = os.path.exists(CONFIGFILE)
    if config_exists:
        try:
            config.read(CONFIGFILE)
            GARMIN_USERNAME = config['GARMIN']['GARMIN_USERNAME']
            GARMIN_PASSWORD = config['GARMIN']['GARMIN_PASSWORD']
            HAMMERHEAD_USERNAME = config['HAMMERHEAD']['HAMMERHEAD_USERNAME']
            HAMMERHEAD_PASSWORD = config['HAMMERHEAD']['HAMMERHEAD_PASSWORD']
        except KeyError:
            print(f'Could not read {CONFIGFILE}. Please check again.')
            sys.exit(1)
    else:
        write_configfile(CONFIGFILE)

    # Set up API clients
    karoo = Karoo(HAMMERHEAD_USERNAME, HAMMERHEAD_PASSWORD)
    garmin = garminconnect.Garmin(GARMIN_USERNAME, GARMIN_PASSWORD)
    garmin.login()

    logger.info(f"Logged into garmin & hammerhead. Garmin display_name: {garmin.display_name}")

    DATA_DIR = "data"
    os.makedirs(DATA_DIR, exist_ok=True)

    for ride in karoo.get_rides():
        ride_id = ride['id']
        logger.info(f"Found ride in Karoo: {ride['name']} [id: {ride_id}]")

        if not os.path.isfile(f"{DATA_DIR}/{ride_id}.fit"):
            fit_file = karoo.download_fit_file(activity_id=ride_id, data_dir=DATA_DIR)

            logger.info("  Uploading to garmin..")
            try:
                garmin.upload_activity(fit_file)
            except garth.exc.GarthHTTPError as e:
                if "409 Client Error" in str(e):
                    logger.info("  Skipping duplicate file")
                else:
                    logger.exception(f"Exception: {str(e)}")
        else:
            logger.info("  This ride was previously downloaded")


if __name__ == "__main__":
    main()
