import os
import pickle
from pyjob import TaskFactory
import logging
from confetti.io import Experiments
from confetti.processing import Sweep


class SweepArray(object):

    def __init__(self, experiments_fname, workdir, platform="sge", queue_name=None, queue_environment=None,
                 max_concurrent_nprocs=1, cleanup=False, dials_exe='dials'):
        self.experiments_fname = experiments_fname
        self.workdir = os.path.join(workdir, 'sweeps')
        self.pickle_fname = os.path.join(self.workdir, 'sweeparray.pckl')
        self.imported_expt = Experiments(experiments_fname)
        self.dials_exe = dials_exe
        self.scripts = []
        self.sweeps = []
        self.queue_name = queue_name
        self.queue_environment = queue_environment
        self.max_concurrent_nprocs = max_concurrent_nprocs
        self.platform = platform
        self.shell_interpreter = "/bin/bash"
        self.cleanup = cleanup
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

    def dump_pickle(self):
        self.make_workdir()
        with open(self.pickle_fname, 'wb') as fhandle:
            pickle.dump(self, fhandle)

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def process_sweeps(self):
        self.make_workdir()

        for idx, experiment in enumerate(self.imported_expt.data, 1):
            if experiment.scan.get_num_images() <= 1:
                continue
            sweep = Sweep(idx, self.workdir)
            sweep.dials_exe = self.dials_exe
            sweep.prepare_input(experiment)
            sweep.dump_pickle()
            self.sweeps.append(sweep)
            self.scripts.append(sweep.script)

        if len(self.scripts) == 0:
            raise ValueError('No sweeps to process!')

        self.logger.info('Processing sweep array')
        with TaskFactory(self.platform, self.scripts, **self._other_task_info) as task:
            task.name = 'sweep-array'
            task.run()

    def reset_wavelength(self, wavelength=None):
        if wavelength is None:
            wavelength = Experiments(self.sweeps[0].integrated_experiments).data[0].beam.get_wavelength()

        for sweep in self.sweeps:
            if sweep.error or not os.path.isfile(sweep.integrated_experiments):
                continue
            sweep_experiments = Experiments(sweep.integrated_experiments)
            for experiment in sweep_experiments.data:
                experiment.beam.set_wavelength(wavelength)
            sweep_experiments.data.as_file(sweep.integrated_experiments)

    def reload_sweeps(self):
        new_sweeps = []
        for sweep in self.sweeps:
            if os.path.isfile(sweep.pickle_fname):
                new_sweeps.append(Sweep('dummy', 'dummy').from_pickle(sweep.pickle_fname))
        self.sweeps = new_sweeps
