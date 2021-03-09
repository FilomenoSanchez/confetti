import os
import subprocess
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class Ctruncate(Wrapper):
    def __init__(self, workdir, hklin, hklout, keywords):
        self.hklin = hklin
        self.hklout = os.path.join(workdir, 'ctruncate', hklout)
        self._keywords = keywords
        self.logcontents = None
        self.ctruncate_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'ctruncate')
        super(Ctruncate, self).__init__(workdir=os.path.join(workdir, 'ctruncate'))

    @property
    def keywords(self):
        return self._keywords

    @property
    def expected_output(self):
        return self.hklout

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'ctruncate_out.log')

    @property
    def cmd(self):
        return "{} -hklin {} -hklout {} {}".format(self.ctruncate_exe, self.hklin, self.hklout, self.keywords)

    def _run(self):
        self.make_workdir()
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)

    def _parse_logfile(self):
        pass
