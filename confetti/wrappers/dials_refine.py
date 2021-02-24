import os
import subprocess
from confetti.wrappers.wrapper import Wrapper


class DialsRefine(Wrapper):

    def __init__(self, workdir, experiments_fname, reflections_fname, scan_varying='false', outlier_algorithm='tukey',
                 dials_exe='dials'):
        self.dials_exe = dials_exe
        self.experiments_fname = experiments_fname
        self.reflections_fname = reflections_fname
        self.scan_varying = scan_varying
        self.outlier_algorithm = outlier_algorithm
        super(DialsRefine, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'refined.expt')

    @property
    def cmd(self):
        return "{dials_exe}.refine {experiments_fname} {reflections_fname} scan_varying={scan_varying} " \
               "outlier.algorithm={outlier_algorithm}".format(**self.__dict__).split()

    def _run(self):
        p = subprocess.Popen(self.cmd)
        p.communicate()

    def _parse_output(self):
        pass
