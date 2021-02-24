import os
import subprocess
from confetti.wrappers.wrapper import Wrapper


class DialsExport(Wrapper):

    def __init__(self, workdir, experiments_fname, reflections_fname, intensity='sum', mtz_hklout='integrated.mtz',
                 dials_exe='dials'):
        self.dials_exe = dials_exe
        self.experiments_fname = experiments_fname
        self.reflections_fname = reflections_fname
        self.intensity = intensity
        self.mtz_hklout = os.path.join(workdir, mtz_hklout)
        super(DialsExport, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return self.mtz_hklout

    @property
    def cmd(self):
        return "{dials_exe}.export {experiments_fname} {reflections_fname} intensity={intensity} " \
               "mtz.hklout={mtz_hklout}".format(**self.__dict__).split()

    def _run(self):
        p = subprocess.Popen(self.cmd)
        p.communicate()

    def _parse_output(self):
        pass
