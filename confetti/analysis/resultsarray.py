import os
import logging
import pandas as pd
from multiprocessing.pool import Pool
from confetti.analysis import Results


class ResultsArray(object):
    def __init__(self, target_id=None, dataset_dir=None):
        self.datasets_dir = dataset_dir
        self.target_id = target_id
        self.table = None
        self.logger = logging.getLogger()

    def process(self, nprocs=1):
        args = []
        for dataset_dir in os.listdir(self.datasets_dir):
            dataset_id = dataset_dir.replace('dataset_', '')
            dataset_dir = os.path.join(self.datasets_dir, dataset_dir)
            if not os.path.isdir(dataset_dir):
                continue
            args.append((dataset_id, dataset_dir))

        with Pool(processes=nprocs) as pool:
            results_tables = pool.starmap(self.recover_results, args)

        self.table = pd.DataFrame()
        for table in results_tables:
            if table is not None:
                self.table = pd.concat([self.table, table])
        self.table['TARGET'] = self.target_id
        self.table.reset_index(drop=True, inplace=True)

    def recover_results(self, dataset_id, dataset_dir):
        mr_dir = os.path.join(dataset_dir, 'mr')
        clusterarray_pickle = os.path.join(dataset_dir, 'clusters', 'clusterarray.pckl')
        completeness_dir = os.path.join(dataset_dir, 'completeness')
        csv_fname = os.path.join(self.datasets_dir, 'results_{}.csv'.format(dataset_id))
        results = Results(dataset_id, clusterarray_pickle, mr_dir, completeness_dir)
        results.process()

        if results.table is not None:
            results.save_csv(csv_fname)
            return results.table
        else:
            return None
