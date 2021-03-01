import os
import pickle
from pyjob import TaskFactory
import logging
from confetti.completeness import Completeness


class CompletenessArray(object):

    def __init__(self, workdir, input_reflections, input_experiments, platform="sge", queue_name=None,
                 queue_environment=None, max_concurrent_nprocs=1, cleanup=False, dials_exe='dials'):
        self.workdir = os.path.join(workdir, 'completeness')
        self.pickle_fname = os.path.join(self.workdir, 'completenessarray.pckl')
        self.scripts = []
        self.completeness_tables = []
        self.queue_name = queue_name
        self.queue_environment = queue_environment
        self.max_concurrent_nprocs = max_concurrent_nprocs
        self.platform = platform
        self.shell_interpreter = "/bin/bash"
        self.dials_exe = dials_exe
        self.cleanup = cleanup
        self.input_reflections = input_reflections
        self.input_experiments = input_experiments
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

    def run(self, expand_to_p1=True):
        self.make_workdir()

        for idx, input_fnames in enumerate(zip(self.input_experiments, self.input_reflections)):
            workdir = os.path.join(self.workdir, 'dataset_{}'.format(idx))
            os.mkdir(workdir)
            dataset = Completeness()
            dataset.is_p1 = expand_to_p1
            dataset.experiments = input_fnames[0]
            dataset.reflections = input_fnames[1]
            dataset.workdir = workdir
            dataset.id = idx
            dataset.csv_out_fname = os.path.join(workdir, 'completeness.csv')
            dataset.dials_exe = self.dials_exe

            self.completeness_tables.append(dataset)
            self.scripts.append(dataset.script)

        if len(self.scripts) == 0:
            raise ValueError('No completeness datasets to process!')

        self.logger.info('Processing dataset completeness')
        with TaskFactory(self.platform, self.scripts, **self._other_task_info) as task:
            task.name = 'completeness-array'
            task.run()

    def reload_tables(self):
        new_tables = []
        for table in self.completeness_tables:
            with open(table.pickle_fname, 'rb') as fhandle:
                new_tables.append(pickle.load(fhandle))
        self.completeness_tables = new_tables
