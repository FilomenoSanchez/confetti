import os
from dials.command_line.dials_import import run
from confetti.wrappers.wrapper import Wrapper


class DialsImport(Wrapper):

    def __init__(self, workdir, input_fnames):
        self.input_fnames = input_fnames
        super(DialsImport, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'imported.expt')

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.import.log')

    @property
    def cmd(self):
        return self.input_fnames.split()

    def _run(self):
        run(self.cmd)

    def _parse_logfile(self):
        pass
