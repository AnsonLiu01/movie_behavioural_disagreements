from datetime import datetime
import os
from typing import Dict, Optional, List
from itertools import islice
import re

from bs4 import BeautifulSoup, ResultSet
from requests import Response
from tqdm import tqdm

import pandas as pd
import numpy as np
from loguru import logger

from src.utils.scraper_utils import ScraperUtility
from src.utils.error_utils import InvalidScrapeTypeError


class RottenTomatoes(ScraperUtility):
    """
    Class for all rotten tomatoes functionalities
    """
    def __init__(
        self,
        tmdb_df: pd.DataFrame
    ):
        """
        :param movie_list: filtered version of the TMDB df
        """
        ScraperUtility.__init__(self)

        self.tmdb_df = tmdb_df
        
        self.url_base = 'https://www.rottentomatoes.com'
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        self.df = None
        self.formatted_releases_dict = None
        self.raw_releases_dict = None
        self.release_found_log = None
        self.movie_name_conflict_list = []
        self.rt_model_format = None
        self.scores_df = None
        self.final_df = None
        self.return_dict = None
    
    def format_releases(self) -> None:
        """
        Function to format all release names to rt-specific url format. Format is simply, no special characters,
        spaces replaced with underscores
        :return: dictionary of movie names & formatted versions
        """
        self.df = self.tmdb_df.copy()

        self.df['formatted_title'] = self.strip_accents(df_col=self.df['title'])
        self.df['formatted_title'] = (self.df['formatted_title']
                                                     .str.lower()
                                                     .str.replace(r'-', r' ')
                                                     .str.replace(r'&', r'and')
                                                     .str.replace(r'/', r' ')
                                                     .str.replace(r'[^a-zA-Z0-9\s]', r'', regex=True)
                                                     .str.replace(r' ', r'_')
                                                     .str.replace(r'_+', r'_', regex=True))

        self.df = self.df.loc[
            self.df['formatted_title'].notna()
            & self.df['formatted_title'].str.strip().ne('')
        ].copy()
        
        df_dupes = self.df[self.df.duplicated(subset=['formatted_title'], keep=False)]
        df_dupes = df_dupes.drop_duplicates(subset=['id'], keep=False)
        
        df_dupes.loc[:, 'formatted_title'] = (
            df_dupes['formatted_title'].astype(str)
            + '_'
            + df_dupes['release_year'].astype(str)
        )
        
        self.df = self.df.loc[~self.df['id'].isin(df_dupes['id'].to_list())]
        
        self.df = pd.concat([self.df, df_dupes])
        self.df = self.df.sort_values(by=['formatted_title'])
    
        dict_df = self.df.set_index('id')

        self.formatted_releases_dict = dict_df['formatted_title'].to_dict()
        self.raw_releases_dict = dict_df['title'].to_dict()

    def make_request(
        self,
        release: str,
        scrape_type: str,
        formatted_release: Optional[str] = None,
        alternative_url: Optional[str] = None
    ) -> Response:
        """
        Function to make a request to RT website
        :param release: raw release name
        :param scrape_type: method of movie scrape i.e. url_match, url_search
        :param formatted_release: formatted release name
        :param alternative_url: options to pass alternative url for movies using 'url_search' method
        :return: Response with URL/webpage info
        """
        if alternative_url:
            url = alternative_url
        else:
            url = os.path.join(self.url_base, 'm', formatted_release) if scrape_type == 'url_match' \
                else self.url_search_builder(formatted_release)

        headers = self.select_random_user_agent()
        response = self.send_request(
            release=release,
            url=url,
            headers=headers
        )

        return response

    def get_tomatometer_and_popcornmeter(self) -> None:
        """
        Function to get the tomato-meter & 'popcornmeter' (audience scores) for each of the target releases
        """
        logger.info(f'Scraping for {self.df.shape[0]} movies')
        
        self.scores_df = self.df[['id', 'title']].copy()

        new_cols = ['Tomatometer', 'Popcornmeter', 'scrape_type']

        for col in new_cols:
            self.df[col] = np.nan

        self.release_found_log = {
            'release_found': [],
            'release_not_found': []
        }

        for id, formatted_release in tqdm(self.formatted_releases_dict.items(), leave=True):
            release = self.raw_releases_dict[id]
            response = self.make_request(release=release, scrape_type='url_match', formatted_release=formatted_release)
            scrape_type = self.verify_release(release, response)

            if scrape_type == 'url_match':
                self.scrape_scores(id=id, release=release, response=response, scrape_type='url_match')
            elif scrape_type == 'url_search':
                r_dt = self.tmdb_df.loc[self.tmdb_df['title'] == release, 'release_year'].to_string(index=False)
                self.search_and_scrape_scores(
                    id=id,
                    release=release,
                    formatted_release=formatted_release,
                    tmdb_release_date=r_dt,
                    scrape_type='url_search'
                )
            else:
                raise InvalidScrapeTypeError('scrape_type must be url_match, url_search or manual_add')

        low_confidence_movies = self.scores_df.loc[
            self.scores_df['Tomatometer'] == '200 - Low confidence in movie found', 'title'].to_list()

        logger.info(f'Movie scores found: {len(self.release_found_log["release_found"])},'
                    f' (of which low confidence: {len(low_confidence_movies)} ({low_confidence_movies}))')

        logger.info(f'Movie scores not found: {len(self.release_found_log["release_not_found"])} '
                    f'({self.release_found_log["release_not_found"]})')

    def verify_release(
        self,
        release: str,
        response: Response,
    ) -> Optional[str]:
        """
        Function to verify the correct url page generated and used.
        :param release: raw release name
        :param response: url info
        :return: type of scrape method ('url_search', 'url_match', 'manual_add' or None if score previously
        scraped/collected)
        """
        soup = BeautifulSoup(response.text, 'html.parser')
        if response.status_code == 200:
            elements = soup.find_all('rt-text', attrs={'slot': 'metadataProp'})
            movie_desc = ', '.join(element.text.lower() for element in elements)

            if release not in self.movie_name_conflict_list:
                release_year = self.get_release_year(movie_desc)
                if release_year >= 2023:
                    return 'url_match'
                else:
                    self.movie_name_conflict_list.append(release)
                    return 'url_search'
            else:
                return None  # Skipping since release already searched for
        else:
            return 'url_search'

    @staticmethod
    def get_release_year(
        movie_desc: str
    ) -> int:
        """
        Function to get the release year. The release year can be extract via different methods
        :return: year of release
        """
        movie_desc_list = movie_desc.split(', ')
        for desc in movie_desc_list:
            if len(desc) == 4 and desc.isdigit():
                return int(desc)
            elif match := re.search(r'\b20\d{2}\b', desc):
                return int(match.group())

        return datetime.now().year

    def scrape_scores(
        self,
        id: int,
        release: str,
        response: Response,
        scrape_type: str,
        url_search_match_score: int = 100
    ) -> None:
        """
        Function to scrape scores
        :param id: id of release
        :param release: raw release name
        :param response: url info
        :param scrape_type: method of movie scrape i.e. url_match, url_search
        :param url_search_match_score: match score if method of scrape came from 'url_search'
        """
        soup = BeautifulSoup(response.text, 'html.parser')

        scorecard = soup.find('media-scorecard').text

        scorecard_stripped = scorecard.strip().replace('\n', '')

        scraped_scores = {
            "Tomatometer": None,
            "Popcornmeter": None,
            "scrape_type": scrape_type,
            "url": response.url,
            "url_search_match_score": url_search_match_score,
        }

        for score_type, score in islice(scraped_scores.items(), 2):
            pattern = rf'(\d{{2,3}})%{re.escape(score_type)}'
            matches = re.findall(pattern, scorecard_stripped)

            scraped_scores[score_type] = matches if matches else 'No score'

        for col_name, value in scraped_scores.items():
            self.scores_df.loc[self.scores_df['id'] == id, col_name] = value

        self.release_found_log['release_found'].append(release)
        # logger.debug(f'{release} - {scrape_type} - found')

    def search_and_scrape_scores(
        self,
        id: int,
        release: str,
        formatted_release: str,
        tmdb_release_date: str,
        scrape_type: str
    ) -> None:
        """
        Function to scrape scores, assumes exact url match not found. Therefore, will utilse bs4's search/query function
        to find the most similar release
        :param id: id of release
        :param release: raw release name
        :param formatted_release: formatted release name
        :param tmdb_release_date: the earliest date for a movie in tmdb df, used to help match to correct movie
        :param scrape_type: method of movie scrape i.e. url_search
        """
        response = self.make_request(
            release=release,
            scrape_type='url_search',
            formatted_release=formatted_release
        )

        new_response = 'No URL found'
        movie_score = 0

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            search_results = soup.find_all('search-page-result', attrs={"type": "movie"})

            if search_results:
                available_movies = search_results[0].find_all('search-page-media-row')  # [1].find_all('a', href=True, attrs={'slot': 'title'})

                url_check_release = f'{formatted_release.replace("_", "")}_{tmdb_release_date}'

                movies_dict = self.label_search_results(available_movies=available_movies)

                best_movie, movie_score = self.get_best_match(url_check_release=url_check_release,
                                                              movie_list=list(movies_dict.keys()))

                new_response = movies_dict.get(best_movie)

                if movie_score >= 75:
                    new_response = self.make_request(
                        release=release,
                        scrape_type='url_match',
                        alternative_url=new_response
                    )

                    self.scrape_scores(
                        id=id,
                        release=release,
                        response=new_response,
                        scrape_type=scrape_type,
                        url_search_match_score=int(movie_score)
                    )
                    return
            bad_response = f'{response.status_code} - Low confidence in movie found'
        else:
            bad_response = f'{response.status_code} - {response.reason}'

        scraped_scores = {
            "Tomatometer": bad_response,
            "Popcornmeter": bad_response,
            "scrape_type": scrape_type,
            "url": new_response,
            "url_search_match_score": movie_score
        }

        for col_name, value in scraped_scores.items():
            self.scores_df.loc[self.scores_df['id'] == id, col_name] = value

        self.release_found_log['release_not_found'].append(release)
        # logger.debug(f'{release} - url_search - not found')

    @staticmethod
    def label_search_results(
        available_movies: ResultSet,
    ) -> Dict:
        """
        Function to uniquely label each search result and place into a dictionary, in order to eventually find the best
        match. The simple while loop ensures that no movie keys are overwritten and increases chances that a more
        relevant movie is picked
        :return: key labelled search results
        """
        movies_dict = {}

        for result in available_movies:
            movie_url = result.find('a', href=True)
            new_response = movie_url['href']

            clean_result = result.find('a', attrs={'slot': 'title'}).text.replace(' ', '').replace('\n', '')
            clean_result = re.sub(r'\s+', ' ', clean_result)
            clean_result = re.sub(r'[^A-Za-z0-9\s]', '', clean_result)
            clean_result = clean_result.lower()
            pattern = r'releaseyear="(\d{4})"'
            rel_year_field = re.search(pattern, str(result))
            rt_release_year = rel_year_field.group(1) if rel_year_field else datetime.now().year

            movie_key = f'{clean_result}_{rt_release_year}'
            suffix = 1
            while movies_dict.get(movie_key):
                suffix += 1
                movie_key = f'{movie_key}_{suffix}'

            movies_dict[movie_key] = new_response

        return movies_dict

    def url_search_builder(
        self,
        formatted_release: str
    ) -> str:
        """
        Function to create a url that produces search results for non-matching releases
        :param formatted_release: formatted release name
        :return: return string that contains full url
        """
        url_release = formatted_release.replace('_', '%20')

        new_search_url = os.path.join(self.url_base, f'search?search={url_release}')

        return new_search_url

    def create_model_formatted_input(self) -> None:
        """
        Function to create a copy of the main dataframe only including necessary data and columns
        """
        self.final_df = self.scores_df[['id', 'title', 'Tomatometer', 'Popcornmeter']].copy()

        pattern = r'^(\d{3}) - [A-Za-z\s]+'
        model_cols = ['Tomatometer', 'Popcornmeter']

        for col in model_cols:
            self.final_df[col] = self.final_df[col].astype(str)
            self.final_df[col] = self.final_df[col].str.replace(pattern, 'No score', regex=True)
            self.final_df = self.final_df.loc[~self.final_df[col].str.contains('no score', na=False, case=False)]
            self.final_df[col] = self.final_df[col].astype(int)
        
    def save(self) -> None:
        """
        Function to save rotten tomatoes scores df to csv
        """
        self.return_dict = {
            'scores': self.scores_df,
            'model': self.final_df
        }
        
        data_dir = os.path.join(self.root_dir, 'data', 'rotten')
        os.makedirs(data_dir, exist_ok=True)

        for type, df in self.return_dict.items():
            file_loc = os.path.join(data_dir, f'{type}_rt.csv')
            
            logger.info(f'Saving {type} df: {file_loc}')
            df.to_csv(file_loc, index=False)
 
    def runner(
        self,
    ) -> pd.DataFrame:
        """
        Main runner function for the rotten tomatoes web scraper
        :return: model-formatted dataframe with rotten tomatoes scores
        """
        self.format_releases()

        self.get_tomatometer_and_popcornmeter()

        self.create_model_formatted_input()

        self.save()

        logger.info('Rotten Tomatoes web scrape completed')

        return self.return_dict
