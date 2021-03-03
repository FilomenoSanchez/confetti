import os
import subprocess
from confetti.wrappers import touch
from confetti.wrappers.wrapper import Wrapper


class Refmac(Wrapper):
    def __init__(self, workdir, hklin, xyzin, low_res, high_res, stdin, hklout='refmac_out.mtz',
                 xyzout='refmac_out.pdb'):
        self.hklin = hklin
        self.hklout = os.path.join(workdir, 'refmac', hklout)
        self.xyzin = xyzin
        self.xyzout = os.path.join(workdir, 'refmac', xyzout)
        self.stdin = stdin
        self.low_res = low_res
        self.high_res = high_res
        self.logcontents = None
        self.refmac_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'refmac5')
        self.rfactor = "NA"
        self.rfree = "NA"
        self.rfactor_delta = ("NA", "NA")
        self.rfree_delta = ("NA", "NA")
        self.bondlenght_delta = ("NA", "NA")
        self.bondangle_delta = ("NA", "NA")
        self.chirvol_delta = ("NA", "NA")
        super(Refmac, self).__init__(workdir=os.path.join(workdir, 'refmac'))

    @property
    def summary(self):
        return self.rfactor, self.rfree

    @property
    def keywords(self):
        return self.stdin.format(**{'LOW_RES': self.low_res, 'HIGH_RES': self.high_res})

    @property
    def expected_output(self):
        return self.xyzout

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'refmac_out.log')

    @property
    def cmd(self):
        return "{} hklin {} hklout {} xyzin {} xyzout {} <<EOF {} " \
               "\nEOF".format(self.refmac_exe, self.hklin, self.hklout, self.xyzin, self.xyzout, self.keywords)

    def _run(self):
        self.make_workdir()
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)

    def _parse_logfile(self):
        reached_end = False
        for line in self.logcontents.decode().split("\n"):
            if "Final results" in line:
                reached_end = True
            elif reached_end and "R factor" in line:
                self.rfactor = float(line.split()[3].rstrip())
                self.rfactor_delta = (float(line.split()[2].rstrip()), self.rfactor)
            elif reached_end and "R free" in line:
                self.rfree = float(line.split()[3].rstrip())
                self.rfree_delta = (float(line.split()[2].rstrip()), self.rfree)
            elif reached_end and "Rms BondLength" in line:
                self.bondlenght_delta = (float(line.split()[2].rstrip()), float(line.split()[3].rstrip()))
            elif reached_end and "Rms BondAngle" in line:
                self.bondangle_delta = (float(line.split()[2].rstrip()), float(line.split()[3].rstrip()))
            elif reached_end and "Rms ChirVolume" in line:
                self.chirvol_delta = (float(line.split()[2].rstrip()), float(line.split()[3].rstrip()))

        # If there is no rfree or rfactor, there was an error
        if self.rfactor == "NA" and self.rfree == "NA":
            self.logger.error("Refmac did not report Rfree and Rfactor !")
            self.error = True
