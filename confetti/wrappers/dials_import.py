import os
import pyjob
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
    def cmd(self):
        return "{dials_exe}.import {input_fnames}".format(**self.__dict__).split()

    def _run(self):
        pyjob.cexec(self.cmd)

    def _parse_output(self):
        pass
