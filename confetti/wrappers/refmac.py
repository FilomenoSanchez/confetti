import os
import subprocess
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class Refmac(Wrapper):
    def __init__(self, workdir, hklin, hklout, xyzin, xyzout, stdin):
        self.hklin = hklin
        self.hklout = os.path.join(workdir, 'refmac', hklout)
        self.xyzin = xyzin
        self.xyzout = os.path.join(workdir, 'refmac', xyzout)
        self.stdin = stdin
        self.logcontents = None
        self.refmac_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'refmac5')
        super(Refmac, self).__init__(workdir=os.path.join(workdir, 'refmac'))

    @property
    def keywords(self):
        return self.stdin

    @property
    def expected_output(self):
        return self.xyzout

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'refmac_out.log')

    @property
    def cmd(self):
        return "{refmac_exe} hklin {hklin} hklout {hklout} xyzin {xyzin} xyzout {xyzout} <<EOF {stdin} " \
               "\nEOF".format(**self.__dict__)

    def _run(self):
        self.make_workdir()
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)

    def _parse_logfile(self):
        pass
