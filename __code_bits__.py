import tarfile
import pandas as pd

with tarfile.open("/Users/ansonliu/Downloads/CMU Movie Summaries.tar.gz", "r:gz") as tar:
    print(tar.getnames())
    
    member = tar.getmember("MovieSummaries/movie.metadata.tsv")
    f = tar.extractfile(member)
    movie_metadata = pd.read_csv(
        f, sep="\t", header=None, dtype=str
    )

movie_metadata.head()

movie_metadata.to_csv('/Users/ansonliu/Github/movie_behavioural_disagreements/data/raw_movie_meta.csv', index=False)

