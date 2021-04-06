import os
from dials.command_line.export import run
from confetti.wrappers.wrapper import Wrapper


class DialsExport(Wrapper):

    def __init__(self, workdir, intensity='sum', mtz_hklout='integrated.mtz'):
        self.input_fnames = 'refined.expt integrated.refl'
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
    def logfile(self):
        return os.path.join(self.workdir, 'dials.export.log')

    @property
    def cmd(self):
        return "{input_fnames} intensity={intensity} mtz.hklout={mtz_hklout}".format(**self.__dict__).split()

    def _run(self):
        run(self.cmd)

    def _parse_logfile(self):
        pass
