import os
import subprocess
from confetti.wrappers.wrapper import Wrapper


class DialsMerge(Wrapper):

    def __init__(self, workdir, input_fnames, dials_exe='dials'):
        self.dials_exe = dials_exe
        self.input_fnames = input_fnames
        self.rpim = 'NA'
        self.rmeas = 'NA'
        self.rmerge = 'NA'
        self.cchalf = 'NA'
        self.i_sigma = 'NA'
        self.multiplicity = 'NA'
        self.completeness = 'NA'
        self.completeness_low = 'NA'
        self.completeness_high = 'NA'
        super(DialsMerge, self).__init__(workdir=workdir)

    @property
    def summary(self):
        return (self.rpim, self.rmeas, self.rmerge, self.cchalf, self.i_sigma, self.multiplicity,
                self.completeness, self.completeness_low, self.completeness_high)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'merged.mtz')

    @property
    def cmd(self):
        return "{dials_exe}.merge {input_fnames}".format(**self.__dict__)

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.merge.log')

    def _run(self):
        p = subprocess.Popen(self.cmd, shell=True)
        p.communicate()

    def _parse_logfile(self):
        with open(self.logfile, 'r') as fhandle:
            for line in fhandle:
                if 'CC half' in line:
                    self.cchalf = float(line.rstrip().lstrip().split()[2])
                elif 'Rpim(I)' in line:
                    self.rpim = float(line.split()[-1].rstrip())
                elif 'Rmeas(I)' in line:
                    self.rmeas = float(line.split()[-1].rstrip())
                elif 'Rmerge(I)' in line:
                    self.rmerge = float(line.split()[-1].rstrip())
                elif 'I/sigma' in line:
                    self.i_sigma = float(line.split()[-1].rstrip())
                elif 'Multiplicity' in line:
                    self.multiplicity = float(line.split()[-1].rstrip())
                elif 'Completeness' in line:
                    self.completeness = float(line.split()[-1].rstrip())
                    self.completeness_high = float(line.split()[3].rstrip())
                    self.completeness_low = float(line.split()[2].rstrip())
