import os
from dials.command_line.merge import run
from confetti.wrappers.wrapper import Wrapper


class DialsMerge(Wrapper):

    def __init__(self, workdir):
        self.input_fnames = 'scaled.expt scaled.refl'
        self.rpim = 'NA'
        self.rmeas = 'NA'
        self.rmerge = 'NA'
        self.cchalf = 'NA'
        self.i_sigma = 'NA'
        self.multiplicity = 'NA'
        self.completeness = 'NA'
        self.completeness_low = 'NA'
        self.completeness_high = 'NA'
        self.space_group = 'NA'
        self.resolution_low = 'NA'
        self.resolution_high = 'NA'
        super(DialsMerge, self).__init__(workdir=workdir)

    @property
    def summary(self):
        return (self.rpim, self.rmeas, self.rmerge, self.cchalf, self.i_sigma, self.multiplicity,
                self.completeness, self.resolution_low, self.resolution_high, self.completeness_low,
                self.completeness_high, self.space_group)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'merged.mtz')

    @property
    def cmd(self):
        return self.input_fnames.split()

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.merge.log')

    def _run(self):
        run(self.cmd)

    def _parse_logfile(self):
        with open(self.logfile, 'r') as fhandle:
            for line in fhandle:
                if 'CC half' in line:
                    self.cchalf = float(line.rstrip().lstrip().split()[2])
                elif 'Rpim(I)' in line:
                    self.rpim = float(line.split()[1].rstrip())
                elif 'Rmeas(I)' in line:
                    self.rmeas = float(line.split()[1].rstrip())
                elif 'Rmerge(I)' in line:
                    self.rmerge = float(line.split()[1].rstrip())
                elif 'I/sigma' in line:
                    self.i_sigma = float(line.split()[1].rstrip())
                elif 'Multiplicity' in line:
                    self.multiplicity = float(line.split()[1].rstrip())
                elif 'Space group number from file:' in line:
                    self.space_group = int(line.rstrip().split()[-1])
                elif 'Resolution range:' in line:
                    self.resolution_low = float(line.split()[-2].rstrip().lstrip())
                    self.resolution_high = float(line.split()[-1].rstrip().lstrip())
                elif 'Completeness' in line and '|' not in line:
                    self.completeness = float(line.split()[1].rstrip())
                    self.completeness_low = float(line.split()[2].rstrip())
                    self.completeness_high = float(line.split()[3].rstrip())
