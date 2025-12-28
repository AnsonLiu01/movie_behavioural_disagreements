import os

from loguru import logger
import pandas as pd


class MergeDataSources:
    """
    Class for all data source merging functions
    """
    def __init__(
        self,
        tmdb_df: pd.DataFrame,
        rt_df: pd.DataFrame
    ) -> None:
        
        self.data_sources = {
            'tmdb': tmdb_df, 
            'rotten': rt_df
            }
           
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        self.merged_df = None
        
    def merge(self) -> None:
        """
        Function to merge all pre-initialised data sources
        """
        logger.info(f'Merging all data sources: {[source for source in self.data_sources.keys()]}')
        self.merged_df = self.data_sources['tmdb'].copy()
        
        logger.info(f'dataset count after mergeing tmdb: {self.merged_df.shape[0]}')
        for source, df in self.data_sources.items():
            if source != 'tmdb':
                self.merged_df = pd.merge(
                    left=self.merged_df,
                    right=df,
                    on='id',
                    how='inner',
                    suffixes=('_x', '_y')
                )

                y_cols = [c for c in self.merged_df.columns if c.endswith('_y')]
                self.merged_df = self.merged_df.drop(columns=y_cols)

                self.merged_df = self.merged_df.rename(
                    columns=lambda c: c[:-2] if c.endswith('_x') else c,
                )
                logger.info(f'dataset count after merging {source}: {self.merged_df.shape[0]}')
        
        logger.success(f'Final movie count: {self.merged_df.shape[0]}')
    
    def save(self) -> None:
        """
        Function to save merged dataset
        """
        model_dir = os.path.join(self.root_dir, 'data', 'model')
        os.makedirs(model_dir, exist_ok=True)

        file_loc = os.path.join(model_dir, 'model_input_df.csv')
            
        logger.info(f'Saving model input df: {file_loc}')
        self.merged_df.to_csv(file_loc, index=False)
        
    def runner(self) -> pd.DataFrame:
        """
        Function to run all merge functions
        :return: merged dataset
        """
        self.merge()
        
        self.save()
        
        return self.merged_df
        
        