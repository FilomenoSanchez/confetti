import os
import pyjob
import json
from confetti.wrappers.wrapper import Wrapper


class DialsCosym(Wrapper):

    def __init__(self, workdir, input_fnames, dials_exe='dials', clustering_threshold=5000, nprocs=1):
        self.dials_exe = dials_exe
        self.input_fnames = input_fnames
        self.clustering_threshold = clustering_threshold
        self.nprocs = nprocs
        self.nclusters = None
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
        return "{dials_exe}.cosym {input_fnames} unit_cell_clustering.threshold={clustering_threshold}" \
               " nproc={nprocs}".format(**self.__dict__).split()

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.cosym.log')

    def _run(self):
        pyjob.cexec(self.cmd)

    def _parse_output(self):
        with open(self.logfile, 'r') as fhandle:
            for line in fhandle:
                if 'clusters:' in line and 'Number of clusters:' not in line:
                    self.nclusters = int(line.rstrip().lstrip().split()[0])
                elif 'Selecting subset of ' in line and ' datasets for cosym analysis:' in line:
                    experiments = line.split('analysis: ')[-1].lstrip().rstrip()
                    self.cluster_experiment_identifiers = json.loads(experiments.replace("'", '"'))
