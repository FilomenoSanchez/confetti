import os
from pyjob import TaskFactory
import logging
from confetti.io import Experiments
from confetti.processing import Sweep


class SweepArray(object):

    def __init__(self, experiments_fname, workdir, platform="sge", queue_name=None, queue_environment=None,
                 max_concurrent_nprocs=1):
        self.experiments_fname = experiments_fname
        self.workdir = workdir
        self.imported_expt = Experiments(experiments_fname)
        self.dials_exe = 'dials'
        self.scripts = []
        self.queue_name = queue_name
        self.queue_environment = queue_environment
        self.max_concurrent_nprocs = max_concurrent_nprocs
        self.platform = platform
        self.shell_interpreter = "/bin/bash"
        self.logger = logging.getLogger()

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

        info = {'directory': self.workdir, 'shell': self.shell_interpreter}

        if self.platform == 'local':
            info['processes'] = self.max_concurrent_nprocs
        else:
            info['max_array_size'] = self.max_concurrent_nprocs
        if self.queue_environment is not None:
            info['environment'] = self.queue_environment
        if self.queue_name is not None:
            info['queue'] = self.queue_name

        return info

    def process_sweeps(self):
        workdir = os.path.join(self.workdir, 'sweeps')
        os.mkdir(workdir)

        for idx, imageset in enumerate(self.imported_expt.imagesets()):

            if imageset.size() == 1:
                continue

            sweep = Sweep(idx, workdir, imageset.paths())
            sweep.dials_exe = self.dials_exe
            sweep.dump_pickle()
            self.scripts.append(sweep.script)

        self.logger.info('Processing sweep array')
        with TaskFactory(self.platform, self.scripts, **self._other_task_info) as task:
            task.name = 'sweep-array'
            task.run()
