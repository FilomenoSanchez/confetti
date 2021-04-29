import os
from dials.command_line.integrate import run
from confetti.wrappers.wrapper import Wrapper


class DialsIntegrate(Wrapper):

    def __init__(self, workdir):
        self.input_fnames = 'refined.expt indexed.refl'
        super(DialsIntegrate, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'integrated.expt')

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.integrate.log')

    @property
    def cmd(self):
        return self.input_fnames.split()

    def _run(self):
        try:
            run(self.cmd)
        except Exception as e:
            self.logger.error('Dials integrate execution found an exception: {}'.format(e))
            self.error = True

    def _parse_logfile(self):
        pass
