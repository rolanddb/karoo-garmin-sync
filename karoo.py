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
        response = self.call_api(url, "POST", headers=headers, payload=payload).json()
        access_token = response['access_token']
        return access_token

    def get_userid(self, token):
        jwt_data = jwt.decode(token, algorithms="HS256", options={"verify_signature": False})
        user = jwt_data['sub']
        return user

    def call_api(self, url, method, headers, payload=None, files=None, params=None):
        try:
            response = requests.request(method, url, headers=headers, data=payload, files=files, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f'Something went wrong: {response.text}')
            sys.exit(1)
        return response

    def get_rides(self):
        logger.info("Getting rides")
        # url = f"https://dashboard.hammerhead.io/v1/users/{user}/activities"
        url = f"https://api.hammerhead.io/users/{self.user}/activities"
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        response = self.call_api(url, "GET", headers=headers)
        response.raise_for_status()
        rides_raw = response.json()

        for ride in rides_raw['data']:
            yield ride

        """
        {'paging': {'self': 'https://api.hammerhead.io/users/102820/activities?page=1&per_page=10', 
        'next': 'https://api.hammerhead.io/users/102820/activities?page=2&per_page=10', 
        'first': 'https://api.hammerhead.io/users/102820/activities?page=1&per_page=10',
         'last': 'https://api.hammerhead.io/users/102820/activities?page=4&per_page=10'}, 
         'totalItems': 35,
          'totalPages': 4,
           'perPage': 10,
            'currentPage': 1, 
        """

        num_pages = rides_raw['totalPages']

        for page in range(2, num_pages + 1):
            logger.info("Getting rides, page {page}")
            url = f"https://dashboard.hammerhead.io/v1/users/{self.user}/activities"
            response = self.call_api(url, "GET", headers=headers, params={'page': page})
            response.raise_for_status()
            rides_raw = response.json()
            for ride in rides_raw['data']:
                yield ride

    def download_fit_file(self, activity_id, data_dir):
        # in rides:
        # {'id': '102820.activity.4259ca9d-34f9-4e4b-8f00-6606783950cd'
        # https://dashboard.hammerhead.io/v1/users/102820/activities/102820.activity.4259ca9d-34f9-4e4b-8f00-6606783950cd/file?format=fit
        url = f"https://dashboard.hammerhead.io/v1/users/{self.user}/activities/{activity_id}/file?format=fit"
        response = self.session.get(url)
        response.raise_for_status()
        response.raw.decode_content = True  # don't try to decode the binary data as text
        filepath = f'{data_dir}/{activity_id}.fit'
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
