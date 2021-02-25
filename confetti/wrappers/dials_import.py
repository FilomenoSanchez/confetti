import os
import subprocess
from confetti.wrappers.wrapper import Wrapper


class DialsImport(Wrapper):

    def __init__(self, workdir, input_fnames, dials_exe='dials'):
        self.dials_exe = dials_exe
        self.input_fnames = input_fnames
        super(DialsImport, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'imported.expt')

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.import.log')

    @property
    def cmd(self):
        return "{dials_exe}.import {input_fnames}".format(**self.__dict__).split()

    def _run(self):
        p = subprocess.Popen(self.cmd)
        p.communicate()

    def _parse_logfile(self):
        pass
