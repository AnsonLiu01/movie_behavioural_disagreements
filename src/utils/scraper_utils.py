import random
import time
from typing import Dict, List, Tuple

import pandas as pd
import requests
from loguru import logger
from rapidfuzz import process, utils, fuzz
from requests import Response
from requests.exceptions import RequestException


class ScraperUtility:
    """
    Utilities class for web scrapers
    """

    def __init__(self):
        self.headers = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9'
        ]

    @staticmethod
    def send_request(
        release: str,
        url: str,
        headers: Dict,
        retries: int = 5,
        backoff_factor: int = 3
    ) -> Response:
        """
        Function to execute the request which contains a backoff if request fails
        :param release: raw release name
        :param url: The URL to make the request to.
        :param headers: A dictionary containing headers to be included in the request.
        :param retries: The number of retry attempts in case of request failure. Default is 5.
        :param backoff_factor: The factor by which the backoff time increases for each retry. Default is 2.
        :return: A Response object representing the HTTP response.
        """
        for retry in range(retries):
            try:
                response = requests.get(url, headers=headers)
                return response
            except RequestException as e:
                if retry < retries - 1:
                    backoff_time = backoff_factor ** retry
                    logger.warning(f'Error occurred requesting for {release}; retrying in {backoff_time} seconds')

                    time.sleep(backoff_time)
                else:
                    logger.warning(f'Maximum times tried: iteration {retry}')
                    raise e

    @staticmethod
    def get_best_match(
        url_check_release: str,
        movie_list: List
    ) -> Tuple[str, int]:
        """
        Function to get best match from potential movie names; utilises fuzzy matching
        :param url_check_release: further formatted version of formatted_release
        :param movie_list: list of potential movie matches
        :return: 'best' movie name match and its score
        """
        best_match = process.extractOne(url_check_release, movie_list, scorer=fuzz.ratio,
                                        processor=utils.default_process)

        return best_match[0], best_match[1]

    @staticmethod
    def strip_accents(df_col: pd.Series) -> pd.Series:
        """
        Function to normalise a string to decompose accented characters - remove any diacritical marks. If there are no
        accented characters then nothing will change
        :param df_col: string to strip accent from
        :return: pd.Series where all characters in all rows are normalised
        """
        return df_col.str.normalize('NFD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    def select_random_user_agent(self) -> Dict:
        """
        Function to get a random user agent to reduce SSL Errors
        :return: dictionary containing selected user agent
        """
        user_agent_dict = {'User-Agent': random.choice(self.headers)}

        return user_agent_dict
