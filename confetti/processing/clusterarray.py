import os
from pyjob import TaskFactory
import logging
from confetti.processing import ClusterSequence


class ClusterArray(object):

    def __init__(self, workdir, sweeps_dir, cluster_thresholds, platform="sge", queue_name=None, queue_environment=None,
                 max_concurrent_nprocs=1, cleanup=False):
        self.sweeps_dir = sweeps_dir
        self.workdir = workdir
        self.dials_exe = 'dials'
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

        info = {'directory': self.workdir, 'shell': self.shell_interpreter, 'cleanup': self.cleanup}

        if self.platform == 'local':
            info['processes'] = self.max_concurrent_nprocs
        else:
            info['max_array_size'] = self.max_concurrent_nprocs
        if self.queue_environment is not None:
            info['environment'] = self.queue_environment
        if self.queue_name is not None:
            info['queue'] = self.queue_name

        return info

    def process_clusters(self):
        workdir = os.path.join(self.workdir, 'clusters')
        os.mkdir(workdir)

        for idx, cluster_threshold in enumerate(self.cluster_thresholds, 1):
            cluster_sequence = ClusterSequence(idx, workdir, self.sweeps_dir, clustering_threshold=cluster_threshold)
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
