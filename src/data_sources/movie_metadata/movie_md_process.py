import os

import pandas as pd


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
        self.df = pd.read_csv(os.path.join(self.root_dir, 'data', self.file_loc))
                
    def clean_data(self) -> None:
        """
        Function to clean and process the data
        """
        keep_cols = [
            'title', 'release_date', 'revenue', 'budget', 'genres', 'production_companies', 'production_countries', 'keywords', 'overview'
        ]
        
        self.df = self.df[keep_cols]
        
        self.df['release'] = self.df['release_date'].str.split('-')[0].astype(int)
        
        self.df = self.df.drop(columns=['release_date'])
        
    def preprocess_runner(self) -> None:
        """
        Sub-runner function for all preprocess functions
        """
        self.load_data()
        
        self.clean_data()
    
    def runner(self) -> None:
        """
        Main runner function
        """
        self.preprocess_runner()
        