import os
import subprocess
from random import randint
from confetti.wrappers import touch, Cad
from confetti.wrappers.wrapper import Wrapper


class Buccaneer(Wrapper):
    def __init__(self, workdir, mtz_fname, refmac_hklout, refmac_xyzout, keywords, xyzout='buccaneer_out.pdb'):
        self.mtz_fname = mtz_fname
        self.refmac_hklout = refmac_hklout
        self.refmac_xyzout = refmac_xyzout
        self.xyzout = os.path.join(workdir, 'buccaneer', xyzout)
        self._keywords = keywords
        self.logcontents = None
        self.buccaneer_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'buccaneer_pipeline')
        self.cad_exe = os.path.join(os.environ.get('CCP4'), 'bin', 'cad')
        self._cad_stdin = '\nLABIN  FILE 1 E1=F E2=SIGF E3=FreeR_flag\nLABIN  FILE 2 E1=PHIC_ALL_LS E2=FOM'
        super(Buccaneer, self).__init__(workdir=os.path.join(workdir, 'buccaneer'))

    # ------------------ General properties ------------------

    @property
    def cad_stdin(self):
        return self._cad_stdin

    @cad_stdin.setter
    def cad_stdin(self, value):
        if value is None:
            pass
        elif not isinstance(value, str):
            raise TypeError('Cad stdin must be a string!')
        else:
            self._cad_stdin = value

    @property
    def keywords(self):
        return self._keywords.format(**{'TITLE': randint(1, 10000), 'XYZIN': self.refmac_xyzout, 'XYZOUT': self.xyzout,
                                        'HKLIN': os.path.join(self.workdir, 'cad', 'buccaneer_input.mtz')})

    @property
    def expected_output(self):
        return self.xyzout

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'buccaneer.log')

    @property
    def cmd(self):
        return "{} {}".format(self.buccaneer_exe, self.keywords)

    # ------------------ General methods ------------------

    def _run(self):
        self.make_workdir()

        cad = Cad(self.workdir, self.mtz_fname, self.refmac_hklout, 'buccaneer_input.mtz', self.cad_stdin)
        cad.run()
        if cad.error:
            self.logger.error('Cad run failed! {}'.format(cad.cmd))
            return

        original_dir = os.getcwd()
        os.chdir(self.workdir)
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.logcontents = p.communicate()[0]
        touch(self.logfile, self.logcontents)
        os.chdir(original_dir)

    def _parse_logfile(self):
        pass
