import os
from dials.command_line.cosym import run
from confetti.wrappers.wrapper import Wrapper
from confetti.io import Experiments


class DialsCosym(Wrapper):

    def __init__(self, workdir, input_fnames, clustering_threshold=5000, nprocs=1):
        self.input_fnames = input_fnames
        self.clustering_threshold = clustering_threshold
        self.nprocs = nprocs
        self.cluster_experiment_identifiers = []
        super(DialsCosym, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'symmetrized.expt')

    @property
    def cmd(self):
        return "{input_fnames} unit_cell_clustering.threshold={clustering_threshold}" \
               " nproc={nprocs}".format(**self.__dict__).split()

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.cosym.log')

    def _run(self):
        try:
            run(self.cmd)
        except Exception as e:
            self.logger.error('Dials cosym execution found an exception: {}'.format(e))

    def _parse_logfile(self):
        if not self.error:
            experiments = Experiments(self.expected_output)
            self.cluster_experiment_identifiers = experiments.identifiers
