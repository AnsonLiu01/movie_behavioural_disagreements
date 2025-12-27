from src.data_sources.movie_metadata.movie_md_process import MovieMetaData
from src.data_sources.rotten_tomatoes.rt_ingest import RottenTomatoes

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
    
    def run(self) -> None:
        """
        Main runner function to process all run types
        """
        if self.run_type == 'ingest':
            self.tmdb = MovieMetaData('raw_movie_meta.csv')
            self.df = self.tmdb.runner()
            
            self.rotten = RottenTomatoes(sorted(self.df['title'].to_list()))
            self.rotten.runner()
            
        if self.run_type in ['ingest', 'model']:
            pass  # TODO: modelling section