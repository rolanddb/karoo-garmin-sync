import logging
import sys

import jwt
import requests

logger = logging.getLogger(__name__)


class Karoo():
    token = None
    user = None
    session = None

    def __init__(self, username, password):
        # Get Hammerhead dashboard access token
        self.token = self.get_access_token(username, password)

        # Get user ID from JWT token
        self.user = self.get_userid(self.token)

        self.session = requests.Session()
        self.session.headers = {
            'Authorization': f'Bearer {self.token}'
        }

    def get_access_token(self, username, password):
        url = "https://dashboard.hammerhead.io/v1/auth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "password",
            "username": username,
            "password": password
        }
        response = requests.post(url, headers=headers, data=payload).json()
        access_token = response['access_token']
        return access_token

    def get_userid(self, token):
        jwt_data = jwt.decode(token, algorithms="HS256", options={"verify_signature": False})
        user = jwt_data['sub']
        return user

    def get_rides(self):
        logger.info("Getting rides")
        url = f"https://api.hammerhead.io/users/{self.user}/activities"
        response = self.session.get(url)
        response.raise_for_status()
        rides_raw = response.json()

        for ride in rides_raw['data']:
            yield ride

        num_pages = rides_raw['totalPages']

        for page in range(2, num_pages + 1):
            logger.info(f"Getting rides, page {page}")
            url = f"https://dashboard.hammerhead.io/v1/users/{self.user}/activities"
            response = self.session.get(url, params={'page': page})
            response.raise_for_status()
            rides_raw = response.json()
            for ride in rides_raw['data']:
                yield ride

    def download_fit_file(self, activity_id, data_dir):
        url = f"https://dashboard.hammerhead.io/v1/users/{self.user}/activities/{activity_id}/file?format=fit"
        response = self.session.get(url)
        response.raise_for_status()
        response.raw.decode_content = True  # don't try to decode the binary data as text
        filepath = f'{data_dir}/{activity_id}.fit'
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
