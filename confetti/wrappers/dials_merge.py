import os
import pyjob
from confetti.wrappers.wrapper import Wrapper


class DialsMerge(Wrapper):

    def __init__(self, workdir, input_fnames, dials_exe='dials'):
        self.dials_exe = dials_exe
        self.input_fnames = input_fnames
        super(DialsMerge, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'merged.mtz')

    @property
    def cmd(self):
        return "{dials_exe}.merge {input_fnames}".format(**self.__dict__).split()

    def _run(self):
        pyjob.cexec(self.cmd)

    def _parse_output(self):
        pass
