import os
import pandas as pd
import pickle
import logging
from confetti.completeness import CompletenessArray
from confetti.processing import SweepArray, ClusterArray
from confetti.mr import MrArray


class Dataset(object):

    def __init__(self, id, workdir, platform="sge", queue_name=None, queue_environment=None, max_concurrent_nprocs=1,
                 cleanup=False, dials_exe='dials'):
        self.workdir = os.path.join(workdir, 'dataset_{}'.format(id))
        self.id = id
        self.sweeparray = None
        self.clusterarray = None
        self.mrarray = None
        self.completeness_array = None
        self.cluster_table = None
        self.mr_table = None
        self.completeness_table = None
        self.queue_name = queue_name
        self.queue_environment = queue_environment
        self.max_concurrent_nprocs = max_concurrent_nprocs
        self.platform = platform
        self.shell_interpreter = "/bin/bash"
        self.dials_exe = dials_exe
        self.cleanup = cleanup
        self.pickle_fname = os.path.join(self.workdir, 'dataset.pckl')
        self.logger = logging.getLogger(__name__)

    # ------------------ Class methods ------------------

    @classmethod
    def from_pickle(cls, pickle_fname):
        with open(pickle_fname, 'rb') as fhandle:
            return pickle.load(fhandle)

    # ------------------ General methods ------------------

    def dump_pickle(self):
        self.make_workdir()
        with open(self.pickle_fname, 'wb') as fhandle:
            pickle.dump(self, fhandle)

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def process_sweeps(self, experiments_fname, sweeps_slice=None, reset_wavelenght=None):
        self.sweeparray = SweepArray(experiments_fname, self.workdir, self.platform, self.queue_name,
                                     self.queue_environment, self.max_concurrent_nprocs, self.cleanup, self.dials_exe)

        if sweeps_slice is not None:
            self.sweeparray.slice_sweeps(sweeps_slice)
        self.sweeparray.process_sweeps()
        if reset_wavelenght is not None:
            self.sweeparray.reset_wavelength(reset_wavelenght)

        self.sweeparray.reload_sweeps()
        self.sweeparray.dump_pickle()

    def process_clusters(self, cluster_thresholds=(100, 200, 300, 500, 1000)):
        self.clusterarray = ClusterArray(self.workdir, self.sweeparray.workdir, cluster_thresholds, self.platform,
                                         self.queue_name, self.queue_environment, self.max_concurrent_nprocs,
                                         self.cleanup, self.dials_exe)

        self.clusterarray.process_clusters()
        self.clusterarray.reload_cluster_sequences()
        self.clusterarray.dump_pickle()

    def run_mr(self, mw, phaser_stdin, refmac_stdin, buccaneer_keywords):
        mtz_list = self.retrieve_unique_mtzs()

        self.mrarray = MrArray(self.workdir, mtz_list, mw, phaser_stdin, refmac_stdin, buccaneer_keywords,
                               self.platform, self.queue_name, self.queue_environment, self.max_concurrent_nprocs,
                               self.cleanup, self.dials_exe)
        self.mrarray.run()
        self.mrarray.reload_mrruns()
        self.mrarray.dump_pickle()

    def process_completeness(self, expand_to_p1=True):
        input_reflections, input_experiments = self.retrieve_scaled_files()
        self.completeness_array = CompletenessArray(self.workdir, input_reflections, input_experiments,
                                                    self.platform, self.queue_name, self.queue_environment,
                                                    self.max_concurrent_nprocs, self.cleanup, self.dials_exe)
        self.completeness_array.run(expand_to_p1)
        self.completeness_array.reload_tables()
        self.completeness_array.dump_pickle()

    def create_cluster_table(self):
        table = []

        for cluster_sequence in self.clusterarray.cluster_sequences:
            for cluster in cluster_sequence.clusters:
                sweeps = []
                for identifier in cluster.experiments_identifiers:
                    sweeps.append(cluster_sequence.sweep_dict[identifier])
                table.append((self.id, cluster_sequence.id, *cluster.summary, tuple(sorted(sweeps))))

        self.cluster_table = pd.DataFrame(table)
        self.cluster_table.columns = ['DATASET', 'CLST_SEQ', 'CLST_ID', 'CLST_THRESHOLD', 'NCLUSTERS',
                                      'CLST_WORKDIR', 'CLST_HKLOUT', 'CLST_SCALED_REFL', 'CLST_SCALED_EXPT',
                                      'RESOLUTION', 'CCHALF_MEAN', 'DELTA_CCHALF_MEAN', 'CCHALF_STD',
                                      'SCALE_N_DELETED_DATASETS', 'RPIM', 'RMEAS', 'RMERGE', 'CCHALF',
                                      'I/SIGMA', 'MULTIPLICITY', 'COMPLETENESS', 'COMPLETENESS_LOW',
                                      'COMPLETENESS_HIGH', 'SPACE_GROUP', 'EXPT_IDS', 'SWEEPS']

    def create_mr_table(self):
        table = []

        for mr_run in self.mrarray.mr_runs:
            table.append((self.id, mr_run.id, *mr_run.summary, mr_run.mtz_fname))

        self.mr_table = pd.DataFrame(table)
        self.mr_table.columns = ['DATASET', 'MR_ID', 'LLG', 'TFZ', 'RFZ', 'eLLG', 'RFMC_RFACT', 'RFMC_RFREE',
                                 'BUCC_RFACT', 'BUCC_RFREE', 'BUCC_COMPLETENESS', 'MR_HKLIN']

    def create_completeness_table(self):
        table = []

        for dataset in self.completeness_array.completeness_tables:
            table.append((self.id, dataset.id, *dataset.summary))

        self.completeness_table = pd.DataFrame(table)
        self.completeness_table.columns = ['DATASET', 'TABLE_ID', 'KSD_r', 'KSD_phi', 'KSD_theta', 'KSD_r_prime']

    def retrieve_unique_mtzs(self):
        mtz_list = []

        if self.cluster_table is None:
            return mtz_list

        clst_mtzs = self.cluster_table.drop_duplicates('SWEEPS').CLST_HKLOUT.tolist()

        for mtz_fname in clst_mtzs:
            if os.path.isfile(mtz_fname):
                mtz_list.append(mtz_fname)

        return mtz_list

    def retrieve_scaled_files(self):
        input_reflections = []
        input_experiments = []

        if self.cluster_table is None:
            return input_reflections, input_experiments

        scaled_refl_list = self.cluster_table.drop_duplicates('SWEEPS').CLST_SCALED_REFL.tolist()
        scaled_expt_list = self.cluster_table.drop_duplicates('SWEEPS').CLST_SCALED_EXPT.tolist()

        for scaled_refl, scaled_expt in zip(scaled_refl_list, scaled_expt_list):
            if os.path.isfile(scaled_expt) and os.path.isfile(scaled_refl):
                input_reflections.append(scaled_refl)
                input_experiments.append(scaled_expt)

        return input_reflections, input_experiments

    def process(self, experiments_fname, mw, phaser_stdin, refmac_stdin, buccaneer_keywords, sweeps_slice=None,
                cluster_thresholds=(100, 200, 300, 500, 1000), reset_wavelenght=None, expand_to_p1=True):
        self.make_workdir()
        self.logger.info('Processing sweeps for dataset {}'.format(self.id))
        self.process_sweeps(experiments_fname, sweeps_slice, reset_wavelenght)
        self.logger.info('Processing clusters for dataset {}'.format(self.id))
        self.process_clusters(cluster_thresholds)
        self.logger.info('Creating cluster table for dataset {}'.format(self.id))
        self.create_cluster_table()
        self.logger.info('Running MR dataset {}'.format(self.id))
        self.run_mr(mw, phaser_stdin, refmac_stdin, buccaneer_keywords)
        self.logger.info('Creating MR results table for dataset {}'.format(self.id))
        self.create_mr_table()
        self.logger.info('Processing completeness for dataset {}'.format(self.id))
        self.process_completeness(expand_to_p1)
        self.logger.info('Creating completeness table for dataset {}'.format(self.id))
        self.create_completeness_table()
