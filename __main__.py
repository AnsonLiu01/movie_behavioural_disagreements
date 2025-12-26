from src.data_sources.movie_metadata.movie_md_process import MovieMetaData

if __name__ == '__main__':
    md = MovieMetaData('raw_movie_meta.csv')
    
    md.runner()