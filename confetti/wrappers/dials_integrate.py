import os
import subprocess
from confetti.wrappers.wrapper import Wrapper


class DialsIntegrate(Wrapper):

    def __init__(self, workdir, experiments_fname, reflections_fname, dials_exe='dials'):
        self.dials_exe = dials_exe
        self.experiments_fname = experiments_fname
        self.reflections_fname = reflections_fname
        super(DialsIntegrate, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'integrated.expt')

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.integrate.log')

    @property
    def cmd(self):
        return "{dials_exe}.integrate {experiments_fname} {reflections_fname}".format(**self.__dict__).split()

    def _run(self):
        p = subprocess.Popen(self.cmd)
        p.communicate()

    def _parse_logfile(self):
        pass
