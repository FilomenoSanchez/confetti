import os
import shutil
import subprocess
import math
from confetti.wrappers import touch, Mtz2Various
from confetti.wrappers.wrapper import Wrapper


class Shelxe(Wrapper):
    def __init__(self, workdir, xyzin, hklin, solvent, nreflections, keywords):
        self.cc = "NA"
        self.acl = "NA"
        self.hklin = hklin
        self.xyzin = xyzin
        self.solvent = solvent
        self.nreflections = nreflections
        self._keywords = keywords
        self.logcontents = None
        self.shelxe_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'shelxe')
        self.mtz2various_stdin = 'LABIN I=IMEAN SIGI=SIGIMEAN FREE=FreeR_flag\nOUTPUT SHELX\nEND'
        super(Shelxe, self).__init__(workdir=os.path.join(workdir, 'shelxe'))

    # ------------------ General properties ------------------

    @property
    def summary(self):
        return self.cc, self.acl

    @property
    def keywords(self):
        return self._keywords.format(**{'SOLVENT': self.solvent, 'NREFLECTIOSN': math.ceil(self.nreflections / 10000)})

    @property
    def input_pda(self):
        return os.path.join(self.workdir, "shelxe-input.pda")

    @property
    def input_hkl(self):
        return os.path.join(self.workdir, "shelxe-input.hkl")

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'shelxe-input.pdb')

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'shelxe.log')

    @property
    def cmd(self):
        return "{} {}".format(self.shelxe_exe, self.keywords)

    # ------------------ General methods ------------------

    def _run(self):
        self.make_workdir()
        original_dir = os.getcwd()
        os.chdir(self.workdir)

        mtz2various = Mtz2Various(self.workdir, self.hklin, self.input_hkl, self.mtz2various_stdin)
        mtz2various.run()
        if mtz2various.error:
            self.logger.error('mtz2various run failed! {}'.format(mtz2various.cmd))
            return

        shutil.copyfile(self.xyzin, self.input_pda)
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)
        os.chdir(original_dir)

    def _parse_logfile(self):
        if self.error:
            return

        with open(self.expected_output, "r") as fhandle:
            for line in fhandle:
                if "TITLE" in line:
                    self.cc = line.split("=")[1].split("%")[0].rstrip().lstrip()
                    shelxe_residues = float(line.split("%")[1].split()[0].rstrip().lstrip())
                    shelxe_chains = int(line.split("%")[1].split()[3].rstrip().lstrip())
                    self.acl = str(round(shelxe_residues / shelxe_chains))
                    break
        fhandle.close()
