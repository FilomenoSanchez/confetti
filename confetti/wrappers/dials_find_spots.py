import os
import pyjob
from confetti.wrappers.wrapper import Wrapper


class DialsFindSpots(Wrapper):

    def __init__(self, workdir, experiments_fname, dials_exe='dials'):
        self.dials_exe = dials_exe
        self.experiments_fname = experiments_fname
        super(DialsFindSpots, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'strong.refl')

    @property
    def cmd(self):
        return "{dials_exe}.find_spots {experiments_fname}".format(**self.__dict__).split()

    def _run(self):
        pyjob.cexec(self.cmd)

    def _parse_output(self):
        pass
