import os
import pickle
from pyjob import TaskFactory
import logging
from confetti.completeness import Completeness
from confetti.wrappers import MtzDump


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

    def prepare_scripts(self, expand_to_p1=True, workdir_template='dataset_{}'):
        self.make_workdir()
        for idx, input_fnames in enumerate(zip(self.input_experiments, self.input_reflections), 1):
            mtz_fname = input_fnames[0].replace('scaled.expt', 'merged.mtz')
            spacegroup = self.get_spacegroup(mtz_fname)
            if expand_to_p1 and spacegroup is not None and spacegroup == 1:
                continue
            workdir = os.path.join(self.workdir, workdir_template.format(idx))
            os.mkdir(workdir)
            dataset = Completeness()
            dataset.is_p1 = expand_to_p1
            dataset.experiments_fname = input_fnames[0]
            dataset.reflections_fname = input_fnames[1]
            dataset.workdir = workdir
            dataset.id = idx
            dataset.csv_out_fname = os.path.join(workdir, 'completeness.csv')
            dataset.dials_exe = self.dials_exe

            self.completeness_tables.append(dataset)
            self.scripts.append(dataset.script)

    def get_spacegroup(self, mtz_fname):
        if os.path.isfile(mtz_fname):
            mtzdump = MtzDump(mtz_fname)
            mtzdump.run()
            return mtzdump.spacegroup
        else:
            return None

    def run(self, expand_to_p1=True):
        self.prepare_scripts(expand_to_p1)

        if len(self.scripts) == 0:
            raise ValueError('No completeness datasets to process!')

        self.logger.info('Processing dataset completeness')
        with TaskFactory(self.platform, self.scripts, **self._other_task_info) as task:
            task.name = 'completeness-array'
            task.run()

    def reload_tables(self):
        new_tables = []
        for table in self.completeness_tables:
            if os.path.isfile(table.csv_out_fname):
                updated_df = Completeness().from_csv(table.csv_out_fname, table.is_p1).table
                table.table = updated_df.copy(True)
                new_tables.append(table)
        self.completeness_tables = new_tables
