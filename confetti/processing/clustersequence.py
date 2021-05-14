import os
import logging
import pickle
import pyjob
from cached_property import cached_property
from confetti.processing import Cluster
from confetti.io import Experiments


class ClusterSequence(object):

    def __init__(self, id, workdir, sweeps_dir, nprocs=1, clustering_threshold=5000):
        self.id = id
        self.sweeps_dir = sweeps_dir
        self.workdir = os.path.join(workdir, 'cluster_sequence_{}'.format(id))
        self.dials_exe = 'dials'
        self.clusters = []
        self.pickle_fname = os.path.join(self.workdir, 'clustersequence.pckl')
        self.nprocs = nprocs
        self.clustering_threshold = clustering_threshold
        self.exclude_sweeps = []
        self.shell_interpreter = "/bin/bash"
        self.logger = logging.getLogger(__name__)

    # ------------------ Class methods ------------------

    @classmethod
    def from_pickle(cls, pickle_fname):
        with open(pickle_fname, 'rb') as fhandle:
            return pickle.load(fhandle)

    # ------------------ General properties ------------------

    @property
    def python_script(self):
        return """{dials_exe}.python << EOF
from confetti.processing import ClusterSequence
cluster_sequence = ClusterSequence('dummy', 'dummy', 'dummy').from_pickle('{pickle_fname}')
cluster_sequence.dials_exe = '{dials_exe}'
cluster_sequence.process()
cluster_sequence.dump_pickle()
EOF""".format(**self.__dict__)

    @property
    def script(self):
        script = pyjob.Script(directory=self.workdir, prefix='cluster_sequence_{}'.format(self.id),
                              stem='', suffix='.sh')
        script.append(self.python_script)
        return script

    @cached_property
    def sweep_dict(self):
        rslt = {}

        for sweep_dir in os.listdir(self.sweeps_dir):
            experiments_fname = os.path.join(self.sweeps_dir, sweep_dir, 'integrated.expt')
            if os.path.isfile(experiments_fname):
                experiment = Experiments(experiments_fname)
                for identifier in experiment.identifiers:
                    rslt[identifier] = sweep_dir

        return rslt

    # ------------------ General methods ------------------

    def dump_pickle(self):
        self.make_workdir()
        with open(self.pickle_fname, 'wb') as fhandle:
            pickle.dump(self, fhandle)

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def process(self):
        self.make_workdir()
        os.chdir(self.workdir)

        idx = 1
        solved = False

        while not solved:

            cluster = Cluster(idx, self.workdir, self.sweeps_dir, self.clustering_threshold, self.nprocs)
            cluster.exclude_sweeps = self.exclude_sweeps
            self.logger.info('Processing Cluster_{}'.format(idx))
            cluster.process()
            self.clusters.append(cluster)
            self.exclude_sweeps += [self.sweep_dict[sweep] for sweep in cluster.experiments_identifiers]

            if len(cluster.experiments_identifiers) <= 1:
                self.logger.info('Cluster_{} found no clusters. Exiting now...'.format(idx))
                solved = True
            elif len(self.exclude_sweeps) >= len(self.sweep_dict.keys()) - 1:
                self.logger.info('All sweeps have been clustered. Exiting now...'.format(idx))
                solved = True
            else:
                self.logger.info('Cluster_{} found more clusters. New iteration...'.format(idx))
                idx += 1
