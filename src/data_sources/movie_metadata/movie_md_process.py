from datetime import datetime
import os

import pandas as pd
from loguru import logger


class MovieMetaData:
    """
    Class for TMDB Movie metadata functions
    """
    def __init__(
        self,
        file_loc: str
    ):
        """
        :param file_loc : file location including base raw movie metadata
        """
        self.file_loc = file_loc
        
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        self.df = None
    
    def load_data(self) -> None:
        """
        Function to load data
        """
        file = os.path.join(self.root_dir, 'data', self.file_loc)
        logger.info(f'Loading main TMDB file: {file}')
             
        self.df = pd.read_csv(file)
                        
    def clean_data(self) -> None:
        """
        Function to clean and process the data
        """
        logger.info('Cleaning data')
        
        keep_cols = [
            'id', 'title', 'release_date', 'revenue', 'budget', 'genres', 'production_companies', 'production_countries', 'keywords', 'overview'
        ]
        
        self.df = self.df[keep_cols]
                
        self.df = self.df.dropna(how="any")
        
        self.df = self.df.loc[self.df['production_countries'].str.contains('United States of America')]
        
        self.df = self.df.drop_duplicates(subset=['id']) 
        
        self.df.loc[:, 'release_year'] = (
            pd.to_datetime(self.df['release_date'], format='%Y-%m-%d')
            .dt.year
        )
        
        self.df = self.df.loc[(self.df['release_year'] >= 2000) & (self.df['release_date'] <= datetime.today().strftime('%Y-%m-%d'))].copy()
        
        self.df = self.df[self.df['revenue'] >= self.df['revenue'].quantile(0.75)]
        
        self.df = self.df.reset_index(drop=True)
        
        logger.info(f'Cleaned data movie count: {self.df["id"].nunique()}')
                
    def preprocess_runner(self) -> None:
        """
        Sub-runner function for all preprocess functions
        """
        self.load_data()
        
        self.clean_data()
    
    def runner(self) -> pd.DataFrame:
        """
        Main runner function
        :return: data frame with cleaned TMDB data
        """
        self.preprocess_runner()
        
        return self.df
        