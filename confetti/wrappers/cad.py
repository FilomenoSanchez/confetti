import os
import subprocess
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class Cad(Wrapper):
    def __init__(self, workdir, hklin1, hklin2, hklout, stdin):
        self.hklin1 = hklin1
        self.hklin2 = hklin2
        self.hklout = hklout
        self.stdin = stdin
        self.logcontents = None
        self.cad_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'cad')
        super(Cad, self).__init__(workdir=os.path.join(workdir, 'cad'))

    @property
    def keywords(self):
        return self.stdin

    @property
    def expected_output(self):
        return self.hklout

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'cad_out.log')

    @property
    def cmd(self):
        return "{cad_exe} hklin1 {hklin1} hklin2 {hklin2} hklout {hklout} <<EOF {stdin} \nEOF".format(**self.__dict__)

    def _run(self):
        self.make_workdir()
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)

    def _parse_logfile(self):
        pass
