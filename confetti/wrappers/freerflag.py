import os
import pyjob
from confetti.wrappers.wrapper import Wrapper


class FreeRFlag(Wrapper):

    def __init__(self, workdir, hklin, hklout):
        self.hklin = os.path.join(workdir, hklin)
        self.hklout = os.path.join(workdir, hklout)
        super(FreeRFlag, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return 'END'

    @property
    def expected_output(self):
        return self.hklout

    @property
    def cmd(self):
        return "freerflag hklin {hklin} hklout {hklout}".format(**self.__dict__).split()

    def _run(self):
        pyjob.cexec(self.cmd, stdin=self.keywords)

    def _parse_output(self):
        pass
