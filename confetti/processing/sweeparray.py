import os
from pyjob import TaskFactory
import logging
from confetti.io import Experiments
from confetti.processing import Sweep


class SweepArray(object):

    def __init__(self, experiments_fname, workdir, platform="sge", queue_name=None, queue_environment=None,
                 max_concurrent_nprocs=1, cleanup=False):
        self.experiments_fname = experiments_fname
        self.workdir = workdir
        self.imported_expt = Experiments(experiments_fname)
        self.dials_exe = 'dials'
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

    def process_sweeps(self):
        workdir = os.path.join(self.workdir, 'sweeps')
        os.mkdir(workdir)

        for idx, imageset in enumerate(self.imported_expt.imagesets, 1):

            if len(imageset) == 1:
                continue

            sweep = Sweep(idx, workdir, imageset)
            sweep.dials_exe = self.dials_exe
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
            if sweep.error:
                continue
            sweep_experiments = Experiments(sweep.integrated_experiments)
            for experiment in sweep_experiments.data:
                experiment.beam.set_wavelength(wavelength)
            sweep_experiments.data.as_file(sweep.integrated_experiments)

    def slice_sweeps(self, slice):
        new_imagesets = []
        for imageset in self.imported_expt.imagesets:
            new_imagesets.append(imageset[slice])
        self.imported_expt.imagesets = tuple(new_imagesets)
