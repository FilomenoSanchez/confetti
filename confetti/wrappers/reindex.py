import os
import subprocess
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class Reindex(Wrapper):
    def __init__(self, workdir, hklin, hklout, spacegroup):
        self.hklin = hklin
        self.hklout = hklout
        self.spacegroup = spacegroup
        self.logcontents = None
        self.reindex_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'reindex')
        super(Reindex, self).__init__(workdir=os.path.join(workdir, 'reindex'))

    @property
    def keywords(self):
        return '\nSYMMETRY {}\nEND\n'.format(self.spacegroup)

    @property
    def expected_output(self):
        return self.hklout

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'reindex.log')

    @property
    def cmd(self):
        return "{} HKLIN {} HKLOUT {} <<EOF {} \nEOF".format(self.reindex_exe, self.hklin, self.hklout, self.keywords)

    def _run(self):
        self.make_workdir()
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)

    def _parse_logfile(self):
        pass
