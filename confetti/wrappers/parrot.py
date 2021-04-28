import os
import subprocess
from random import randint
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class Parrot(Wrapper):
    def __init__(self, workdir, hklin, seqin, solvent, hklout='parrot_out.mtz'):
        self.hklin = hklin
        self.seqin = seqin
        self.solvent = solvent
        self.hklout = os.path.join(workdir, 'parrot', hklout)
        self.logcontents = None
        self.parrot_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'cparrot')
        super(Parrot, self).__init__(workdir=os.path.join(workdir, 'parrot'))

    # ------------------ General properties ------------------

    @property
    def summary(self):
        return None

    @property
    def _keywords(self):
        return "-title {TITLE} -pdbin-ref $CCP4/lib/data/reference_structures/reference-1tqw.pdb " \
               "-mtzin-ref $CCP4/lib/data/reference_structures/reference-1tqw.mtz " \
               "-colin-ref-fo FP.F_sigF.F,FP.F_sigF.sigF -colin-ref-hl FC.ABCD.A,FC.ABCD.B,FC.ABCD.C,FC.ABCD.D " \
               "-seqin {SEQIN} -mtzin {HKLIN} -solvent-content {SOLVENT} -colout parrot -mtzout {HKLOUT} " \
               "-colin-fo '/*/*/[F,SIGF]' -colin-phifom '/*/*/[PHIC_ALL_LS,FOM]' " \
               "-colin-fc '/*/*/[FWT,PHWT]' -colin-free '/*/*/[FreeR_flag]' " \
               "-solvent-flatten -ncs-average -ncs-mask-filter-radius 6 -resolution 1 " \
               "-cycles 3 -histogram-match -anisotropy-correction"

    @property
    def keywords(self):
        return self._keywords.format(**{'TITLE': randint(1, 10000), 'SEQIN': self.seqin, 'SOLVENT': self.solvent,
                                        'HKLIN': self.hklin, 'HKLOUT': self.hklout})

    @property
    def expected_output(self):
        return self.hklout

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'parrot.log')

    @property
    def cmd(self):
        return "{} {}".format(self.parrot_exe, self.keywords)

    # ------------------ General methods ------------------

    def _run(self):
        self.make_workdir()
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)

    def _parse_logfile(self):
        pass
