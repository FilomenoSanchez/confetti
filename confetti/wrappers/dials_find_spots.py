import os
from dials.command_line.find_spots import run
from confetti.wrappers.wrapper import Wrapper


class DialsFindSpots(Wrapper):

    def __init__(self, workdir):
        self.experiments_fname = ['imported.expt']
        super(DialsFindSpots, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.find_spots.log')

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'strong.refl')

    @property
    def cmd(self):
        return self.experiments_fname

    def _run(self):
        try:
            run(self.cmd)
        except Exception as e:
            self.logger.error('Dials find spots execution found an exception: {}'.format(e))
            self.error = True

    def _parse_logfile(self):
        pass
