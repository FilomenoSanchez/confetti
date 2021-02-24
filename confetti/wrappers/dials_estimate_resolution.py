import os
import subprocess
from confetti.wrappers.wrapper import Wrapper


class DialsEstimateResolution(Wrapper):

    def __init__(self, workdir, input_fnames, dials_exe='dials'):
        self.dials_exe = dials_exe
        self.input_fnames = input_fnames
        self.resolution = None
        super(DialsEstimateResolution, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'dials.estimate_resolution.log')

    @property
    def cmd(self):
        return "{dials_exe}.estimate_resolution {input_fnames}".format(**self.__dict__).split()

    def _run(self):
        p = subprocess.Popen(self.cmd, shell=True)
        p.communicate()

    def _parse_output(self):
        with open(self.expected_output, 'r') as fhandle:
            for line in fhandle:
                if 'Resolution cc_half:' in line:
                    self.resolution = line.rstrip().split()[-1]
