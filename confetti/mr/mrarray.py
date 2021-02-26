import os
import pickle
from pyjob import TaskFactory
import logging
from confetti.mr import MrRun


class MrArray(object):

    def __init__(self, workdir, mtz_list, mw, phaser_stdin, refmac_stdin, buccaneer_keywords, platform="sge",
                 queue_name=None, queue_environment=None, max_concurrent_nprocs=1, cleanup=False, dials_exe='dials'):
        self.workdir = os.path.join(workdir, 'mr')
        self.pickle_fname = os.path.join(self.workdir, 'mrarray.pckl')
        self.ccp4_bin = os.path.join(os.environ.get('CCP4'), 'bin')
        self.scripts = []
        self.mr_runs = []
        self.queue_name = queue_name
        self.queue_environment = queue_environment
        self.max_concurrent_nprocs = max_concurrent_nprocs
        self.platform = platform
        self.shell_interpreter = "/bin/bash"
        self.dials_exe = dials_exe
        self.cleanup = cleanup
        self.mtz_list = mtz_list
        self.mw = mw
        self.phaser_stdin = phaser_stdin
        self.refmac_stdin = refmac_stdin
        self.buccaneer_keywords = buccaneer_keywords
        self.logger = logging.getLogger(__name__)

    # ------------------ Class methods ------------------

    @classmethod
    def from_pickle(cls, pickle_fname):
        with open(pickle_fname, 'rb') as fhandle:
            return pickle.load(fhandle)

    # ------------------ General properties ------------------

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

    # ------------------ General methods ------------------

    def dump_pickle(self):
        self.make_workdir()
        with open(self.pickle_fname, 'wb') as fhandle:
            pickle.dump(self, fhandle)

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def run(self):
        self.make_workdir()

        for idx, mtz_fname in enumerate(self.mtz_list, 1):
            mr_run = MrRun(idx, self.workdir, mtz_fname, self.mw, self.phaser_stdin,
                           self.refmac_stdin, self.buccaneer_keywords)
            mr_run.dials_exe = self.dials_exe
            mr_run.dump_pickle()

            self.mr_runs.append(mr_run)
            self.scripts.append(mr_run.script)

        self.logger.info('Processing mr array')
        with TaskFactory(self.platform, self.scripts, **self._other_task_info) as task:
            task.name = 'mr-array'
            task.run()
