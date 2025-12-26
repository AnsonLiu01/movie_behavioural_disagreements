import os

import pandas as pd


class MovieMetaData:
    """
    Class for Movie metadata functions
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
        
    def process_col_names(self) -> None: 
        """
        Function to add column names to raw data frame
        """
        col_names = ['wiki_movie_id', 'freebase_movie_id', 'name', 'release_date', 'revenue', 'runtime', 'languages', 'countries', 'genres']
        relevant_cols = ['name', 'release_date', 'revenue', 'runtime', 'genres']
        
        self.df.columns = col_names
        
        self.df = self.df[relevant_cols]
        
    def clean_data(self) -> None:
        """
        Function to clean and process the data
        """
        self.df["release_year"] = (
            self.df["release_date"]
            .astype(str)
            .str.extract(r"(\d{4})")
            .fillna('9999')
            .astype(int)
        )

        self.df["genres_list"] = self.df["genres"].fillna("").astype(str).str.findall(r':\s*"([^"]+)"')

        mask_dicts = self.df["genres"].apply(lambda x: isinstance(x, dict))
        if mask_dicts.any():
            self.df.loc[mask_dicts, "genres_list"] = self.df.loc[mask_dicts, "genres"].apply(lambda d: list(d.values()))

        self.df["genres_list"] = self.df["genres_list"].apply(
            lambda lst: [g.strip().lower() for g in dict.fromkeys(lst)] if isinstance(lst, list) else []
        )
        
        self.df = self.df[['name', 'release_year', 'genres_list', 'revenue']]
        
    def preprocess_runner(self) -> None:
        """
        Sub-runner function for all preprocess functions
        """
        self.load_data()
        
        self.process_col_names()

        self.clean_data()
    
    def runner(self) -> None:
        """
        Main runner function
        """
        self.preprocess_runner()
        