from src.data_sources.movie_metadata.movie_md_process import MovieMetaData
from src.data_sources.rotten_tomatoes.rt_ingest import RottenTomatoes
from src.data_sources.merge_sources.merge_data_sources import MergeDataSources

class Runner:
    """
    Main Runner Class
    """
    def __init__(
        self,
        run_type: str
        ):
        self.run_type = run_type
        
        self.df = None

        self.tmdb = None        
        self.rotten = None
        self.merge_sources = None
        
        self.tmdb_df = None
        self.scores_dict = None
        self.model_input_df = None
    
    def run(self) -> None:
        """
        Main runner function to process all run types
        """
        if self.run_type == 'ingest':
            self.tmdb = MovieMetaData('tmdb_movies.csv')
            self.tmdb_df = self.tmdb.runner()
            
            self.rotten = RottenTomatoes(self.tmdb_df[['id', 'title', 'release_year']])
            self.scores_dict = self.rotten.runner()
            
            self.merge_sources = MergeDataSources(
                tmdb_df=self.tmdb_df.copy(),
                rt_df=self.scores_dict['model'].copy()
            )
            self.model_input_df = self.merge_sources.runner()
            
        if self.run_type in ['ingest', 'model']:
            pass