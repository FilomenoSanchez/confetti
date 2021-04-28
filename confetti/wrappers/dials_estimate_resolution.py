import os
from dials.command_line.estimate_resolution import run
from confetti.wrappers.wrapper import Wrapper


class DialsEstimateResolution(Wrapper):

    def __init__(self, workdir):
        self.input_fnames = 'symmetrized.expt symmetrized.refl'
        self.resolution = None
        super(DialsEstimateResolution, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.estimate_resolution.log')

    @property
    def expected_output(self):
        return self.logfile

    @property
    def cmd(self):
        return self.input_fnames.split()

    def _run(self):
        run(self.cmd)

    def _parse_logfile(self):
        with open(self.logfile, 'r') as fhandle:
            for line in fhandle:
                if 'Resolution cc_half:' in line:
                    self.resolution = float(line.rstrip().split()[-1])
