import os
import subprocess
from enum import Enum
import gemmi
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class PhaserScores(Enum):
    """An enumerator that contains the figures of merit to be parsed from phaser logfile"""

    LLG = 'LLG'
    TFZ = 'TFZ'
    RFZ = 'RFZ'


class Phaser(Wrapper):
    def __init__(self, workdir, ncopies, mw, mtz_fname, stdin, root='phaser_out'):
        self.ncopies = ncopies
        self.mw = mw
        self.mtz_fname = mtz_fname
        self.stdin = stdin
        self.root = root
        self.logcontents = None
        self.RFZ = "NA"
        self.TFZ = "NA"
        self.LLG = "NA"
        self.eLLG = "NA"
        self.VRMS = "NA"
        self.phaser_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'phaser')
        super(Phaser, self).__init__(workdir=os.path.join(workdir, 'phaser'))

    @property
    def summary(self):
        return self.LLG, self.TFZ, self.RFZ, self.eLLG

    @property
    def output_spacegroup(self):
        if os.path.isfile(self.hklout):
            mtz = gemmi.read_mtz_file(self.hklout)
            return mtz.spacegroup.number
        else:
            return None

    @property
    def keywords(self):
        return self.stdin.format(**{'COPIES': self.ncopies, 'MW': self.mw, 'HKLIN': self.mtz_fname})

    @property
    def expected_output(self):
        return os.path.join(self.workdir, '{}.1.pdb'.format(self.root))

    @property
    def hklout(self):
        return os.path.join(self.workdir, '{}.1.mtz'.format(self.root))

    @property
    def logfile(self):
        return os.path.join(self.workdir, '{}.log'.format(self.root))

    @property
    def cmd(self):
        return "{}<<EOF {} \nEOF".format(self.phaser_exe, self.keywords)

    def _run(self):
        self.make_workdir()
        original_dir = os.getcwd()
        os.chdir(self.workdir)
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)
        os.chdir(original_dir)

    def _parse_logfile(self):

        # Parse the pdbout for LLG, TFZ and RFZ
        figures_of_merit_remark = []
        llg_remark = []
        if os.path.isfile(self.expected_output):
            with open(self.expected_output, "r") as fhandle:
                lines = fhandle.readlines()
            llg_remark = [x for x in lines if 'REMARK' in x and "Log-Likelihood Gain" in x]
            figures_of_merit_remark = [x for x in lines if ('REMARK' in x) and ("TFZ" in x or "RFZ" in x)]

        if not any(figures_of_merit_remark):
            self.error = True
            self.logger.error('Cannot find REMARK entry with figures of merit!')
            return

        for attribute in PhaserScores:
            values = [x for x in figures_of_merit_remark[0].split() if '%s=' % attribute.value in x]
            if any(values):
                self.__setattr__(attribute.value, values[-1].split("=")[-1].rstrip().lstrip())

        if any(llg_remark):
            self.LLG = llg_remark[0].split()[-1].rstrip().lstrip()

        # Parse the logfile for eLLG and VRMS
        ellg_reached = False
        for line in self.logcontents.decode().split("\n"):
            line = line.rstrip().lstrip()
            if "eLLG   RMSD frac-scat  Ensemble" in line:
                ellg_reached = True
            elif ellg_reached:
                self.eLLG = line.split()[0]
                ellg_reached = False
            if "SOLU ENSEMBLE" in line and "VRMS DELTA" in line:
                self.VRMS = line.split()[5].rstrip().lstrip()
                break

        if self.LLG == "NA" or self.TFZ == "NA":
            self.logger.error("Unable to parse TFZ (%s) and LLG (%s)" % (self.TFZ, self.LLG))
            self.error = True
