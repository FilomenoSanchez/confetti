import os
import pickle
from pyjob import TaskFactory
import logging
from confetti.processing import ClusterSequence


class ClusterArray(object):

    def __init__(self, workdir, sweeps_dir, cluster_thresholds, platform="sge", queue_name=None, queue_environment=None,
                 max_concurrent_nprocs=1, cleanup=False, dials_exe='dials'):
        self.sweeps_dir = sweeps_dir
        self.workdir = os.path.join(workdir, 'clusters')
        self.pickle_fname = os.path.join(self.workdir, 'clusterarray.pckl')
        self.dials_exe = dials_exe
        self.scripts = []
        self.cluster_sequences = []
        self.queue_name = queue_name
        self.queue_environment = queue_environment
        self.max_concurrent_nprocs = max_concurrent_nprocs
        self.platform = platform
        self.shell_interpreter = "/bin/bash"
        self.cleanup = cleanup
        self.cluster_thresholds = cluster_thresholds
        self.logger = logging.getLogger(__name__)

    # ------------------ Class methods ------------------

    @classmethod
    def from_pickle(cls, pickle_fname):
        with open(pickle_fname, 'rb') as fhandle:
            return pickle.load(fhandle)

    # ------------------ General properties ------------------

    @property
    def dials_exe(self):
        return self._dials_exe

    @dials_exe.setter
    def dials_exe(self, value):
        if value is None:
            pass
        elif not isinstance(value, str):
            raise TypeError('Dials exe must be a string!')
        else:
            self._dials_exe = value

    @property
    def _other_task_info(self):
        """A dictionary with the extra kwargs for :py:obj:`pyjob.TaskFactory`"""

        info = dict(directory=self.workdir, shell=self.shell_interpreter, cleanup=self.cleanup)

        if self.platform == 'local':
            info['processes'] = self.max_concurrent_nprocs
        else:
            info['max_array_size'] = self.max_concurrent_nprocs
        if self.queue_environment is not None:
            info['environment'] = self.queue_environment
        if self.queue_name is not None:
            info['queue'] = self.queue_name

        return info

    # ------------------ General methods ------------------

    def dump_pickle(self):
        self.make_workdir()
        with open(self.pickle_fname, 'wb') as fhandle:
            pickle.dump(self, fhandle)

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def process_clusters(self):

        self.make_workdir()

        for idx, cluster_threshold in enumerate(self.cluster_thresholds, 1):
            cluster_sequence = ClusterSequence(idx, self.workdir,
                                               self.sweeps_dir, clustering_threshold=cluster_threshold)
            cluster_sequence.dials_exe = self.dials_exe
            cluster_sequence.dump_pickle()

            self.cluster_sequences.append(cluster_sequence)
            self.scripts.append(cluster_sequence.script)

        if len(self.scripts) == 0:
            raise ValueError('No clustering sequences to process!')

        self.logger.info('Processing clustering array')
        with TaskFactory(self.platform, self.scripts, **self._other_task_info) as task:
            task.name = 'cluster-array'
            task.run()

    def reload_cluster_sequences(self):
        new_clst_seq = []
        for cluster_sequence in self.cluster_sequences:
            new_clst_seq.append(ClusterSequence('dummy', 'dummy', 'dummy').from_pickle(cluster_sequence.pickle_fname))
        self.cluster_sequences = new_clst_seq
