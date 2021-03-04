import os
import subprocess
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class MtzDump(Wrapper):
    def __init__(self, hklin):
        self.hklin = hklin
        self.logcontents = None
        self.spacegroup = None
        self.mtzdmp_exe = os.path.join(os.environ.get('CCP4'), 'etc', 'mtzdmp')
        super(MtzDump, self).__init__(workdir=os.environ.get('CCP4'))

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return None

    @property
    def logfile(self):
        return None

    @property
    def cmd(self):
        return "{mtzdmp_exe} {hklin}".format(**self.__dict__)

    def _run(self):
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]

    def _parse_logfile(self):
        for line in self.logcontents.decode().split("\n"):
            line = line.rstrip().lstrip()
            if "* Space group =" in line:
                self.spacegroup = int(line.split()[-1].replace(')', ''))
