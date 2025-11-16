from typing import List

import pandas as pd


class RottenTomatoes:
    """
    Class for all rotten tomatoes functionalities
    """
    def __init__(
        self,
        movie_list: List
    ):
        """
        :param movie_list: list of movies to scrape
        """
        self.movie_list = movie_list
        
        self.df = None
    
    def runner(self) -> None:
        """
        Main runner function
        """
        #TODO: create other functions