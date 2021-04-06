import os
from dials.commnad_line.refine import run
from confetti.wrappers.wrapper import Wrapper


class DialsRefine(Wrapper):

    def __init__(self, workdir, scan_varying='false', outlier_algorithm='tukey'):
        self.input_fnames = 'indexed.expt indexed.refl'
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
    def logfile(self):
        return os.path.join(self.workdir, 'dials.refine.log')

    @property
    def cmd(self):
        return "{input_fnames} scan_varying={scan_varying} " \
               "outlier.algorithm={outlier_algorithm}".format(**self.__dict__).split()

    def _run(self):
        run(self.cmd)

    def _parse_logfile(self):
        pass
