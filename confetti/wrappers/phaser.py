import os
import subprocess
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class Phaser(Wrapper):
    def __init__(self, workdir, stdin, root='phaser_out'):
        self.workdir = os.path.join(workdir, 'phaser')
        self.stdin = stdin
        self.root = root
        self.logcontents = None
        self.phaser_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'phaser')
        super(Phaser, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, '{}.1.pdb'.format(self.root))

    @property
    def logfile(self):
        return os.path.join(self.workdir, '{}.1.log')

    @property
    def expected_output(self):
        return self.hklout

    @property
    def cmd(self):
        return "{phaser_exe}<<EOF {stdin} \nEOF".format(**self.__dict__).split()

    def _run(self):
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)

    def _parse_logfile(self):
        pass
