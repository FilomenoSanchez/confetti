import os
import subprocess
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class Mtz2Various(Wrapper):
    def __init__(self, workdir, hklin, hklout, stdin):
        self.hklin1 = hklin
        self.hklout = hklout
        self.stdin = stdin
        self.logcontents = None
        self.mtz2various_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'mtz2various')
        super(Mtz2Various, self).__init__(workdir=os.path.join(workdir, 'mtz2various'))

    @property
    def keywords(self):
        return self.stdin

    @property
    def expected_output(self):
        return self.hklout

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'mtz2various.log')

    @property
    def cmd(self):
        return "{mtz2various_exe} HKLIN {hklin} HKLOUT {hklout} <<EOF {stdin} \nEOF".format(**self.__dict__)

    def _run(self):
        self.make_workdir()
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)

    def _parse_logfile(self):
        pass
