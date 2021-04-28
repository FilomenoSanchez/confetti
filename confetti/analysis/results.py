import os
import logging
import pickle
import pandas as pd
import json
from confetti.completeness import Completeness


class Results(object):
    def __init__(self, dataset_id=None, clusterarray_pickle=None, mr_dir=None, completeness_dir=None):
        self.dataset_id = dataset_id
        self.mr_dir = mr_dir
        self.completeness_dir = completeness_dir
        self.clusterarray_pickle = clusterarray_pickle
        self.table = None
        self.mr_table = None
        self.cluster_table = None
        self.completeness_table = None
        self.logger = logging.getLogger()

    # ------------------ Class methods ------------------

    @classmethod
    def from_csv(cls, csv_fname):
        table = pd.read_csv(csv_fname)
        results = Results()
        results.table = table
        return results

    # ------------------ General methods ------------------

    def save_csv(self, csv_fname):
        if self.table is None:
            self.logger.error('No results table found!')
        else:
            self.table.to_csv(csv_fname)

    def recover_completeness(self):
        if self.completeness_dir is None:
            self.logger.error('No completeness dir to parse')
            return

        completeness_table = []
        for completeness_table_dir in os.listdir(self.completeness_dir):
            table_id = completeness_table_dir.replace('_p1', '').split('_')[-1]
            completeness_table_csv = os.path.join(self.completeness_dir, completeness_table_dir, 'completeness.csv')
            script_fname = os.path.join(self.completeness_dir, completeness_table_dir,
                                        'completeness_table_{}.sh'.format(table_id))
            if os.path.isfile(completeness_table_csv):
                with open(script_fname, 'r') as fhandle:
                    for line in fhandle:
                        if 'completeness = Completeness().from_raw_data' in line:
                            line = line[43:].rstrip().replace("'", '"').replace('(', '[').replace(')', ']') \
                                .replace('True', 'true').replace('False', 'false')
                            input_args = json.loads(line)
                            reflections_fname = input_args[1]
                            experiments_fname = input_args[0]
                            is_p1 = input_args[2]
                            break
                updated_completeness = Completeness().from_csv(completeness_table_csv, is_p1)
                updated_completeness.reflections_fname = reflections_fname
                updated_completeness.experiments_fname = experiments_fname
                completeness_table.append((self.dataset_id, table_id, *updated_completeness.summary))

        self.completeness_table = pd.DataFrame(completeness_table)
        self.completeness_table.columns = ['DATASET', 'TABLE_ID', 'IS_P1', 'SCALED_REFL', 'SCALED_EXPT', 'KSD_r',
                                           'KSD_phi', 'KSD_theta', 'KSD_r_prime', 'R_RFLmissing_0.3',
                                           'R_RFLmissing_0.6', 'R_RFLmissing_0.9', 'R_VOLUME']
        self.completeness_table.drop('DATASET', 1, inplace=True)

    def recover_clusters(self):
        if self.clusterarray_pickle is None:
            self.logger.error('No cluster array pickle to load')
            return

        cluster_table = []
        with open(self.clusterarray_pickle, 'rb') as fhandle:
            clusterarray = pickle.load(fhandle)

        for cluster_sequence in clusterarray.cluster_sequences:
            for cluster in cluster_sequence.clusters:
                sweeps = []
                for identifier in cluster.experiments_identifiers:
                    sweeps.append(cluster_sequence.sweep_dict[identifier])
                cluster_table.append((self.dataset_id, cluster_sequence.id, *cluster.summary, tuple(sorted(sweeps))))

        self.cluster_table = pd.DataFrame(cluster_table)
        self.cluster_table.columns = ['DATASET', 'CLST_SEQ', 'CLST_ID', 'CLST_THRESHOLD', 'NCLUSTERS',
                                      'CLST_WORKDIR', 'CLST_HKLOUT', 'CLST_SCALED_REFL', 'CLST_SCALED_EXPT',
                                      'CCHALF_MEAN', 'DELTA_CCHALF_MEAN', 'CCHALF_STD', 'SCALE_N_DELETED_DATASETS',
                                      'RPIM', 'RMEAS', 'RMERGE', 'CCHALF', 'I/SIGMA', 'MULTIPLICITY', 'COMPLETENESS',
                                      'RESOLUTION_LOW', 'RESOLUTION_HIGH', 'COMPLETENESS_LOW', 'COMPLETENESS_HIGH',
                                      'SPACE_GROUP', 'EXPT_IDS', 'SWEEPS']
        self.cluster_table.reset_index(drop=True, inplace=True)

    def recover_mr_results(self):
        if self.mr_dir is None:
            self.logger.error('No mr dir to parse')
            return

        mr_table = []
        for mr_run_dir in os.listdir(self.mr_dir):
            mr_run_dir = os.path.join(self.mr_dir, mr_run_dir)
            mr_pickle = os.path.join(mr_run_dir, 'mrrun.pckl')
            if os.path.isfile(mr_pickle):
                try:
                    with open(mr_pickle, 'rb') as fhandle:
                        mr = pickle.load(fhandle)
                        if mr.shelxe is not None and mr.shelxe.logcontents is not None:
                            mr_table.append((self.dataset_id, mr.id, mr.searchmodel, *mr.summary, mr.mtz_fname))
                except MemoryError:
                    continue

        self.mr_table = pd.DataFrame(mr_table)
        self.mr_table.columns = ['DATASET', 'MR_ID', 'SEARCHMODEL', 'LLG', 'TFZ', 'RFZ', 'eLLG', 'RFMC_RFACT',
                                 'RFMC_RFREE', 'SHELXE_CC', 'SHELXE_ACL', 'BUCC_RFACT', 'BUCC_RFREE',
                                 'BUCC_COMPLETENESS', 'MR_HKLIN']
        self.mr_table.drop('DATASET', 1, inplace=True)

    def process(self):
        self.recover_mr_results()
        self.recover_completeness()
        self.recover_clusters()

        if any([True for x in (self.mr_table, self.cluster_table, self.completeness_table) if x is None]):
            self.logger.error('Missing data, unable to continue')
            return

        self.table = self.cluster_table.merge(self.mr_table, left_on='CLST_HKLOUT', right_on='MR_HKLIN', how='inner')
        self.table = self.table.merge(self.completeness_table, left_on='CLST_SCALED_REFL', right_on='SCALED_REFL',
                                      how='inner')
        self.table.reset_index(drop=True, inplace=True)
