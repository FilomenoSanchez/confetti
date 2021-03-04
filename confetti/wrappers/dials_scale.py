import os
import subprocess
import json
from confetti.wrappers.wrapper import Wrapper


class DialsScale(Wrapper):

    def __init__(self, workdir, experiments_fname, reflections_fname, d_min, dials_exe='dials', nprocs=1,
                 filtering_method='deltacchalf', deltacchalf_mode='dataset', deltacchalf_stdcutoff=3,
                 deltacchalf_max_cycles=10):
        self.dials_exe = dials_exe
        self.experiments_fname = experiments_fname
        self.reflections_fname = reflections_fname
        self.d_min = d_min
        self.nprocs = nprocs
        self.filtering_method = filtering_method
        self.deltacchalf_mode = deltacchalf_mode
        self.deltacchalf_stdcutoff = deltacchalf_stdcutoff
        self.deltacchalf_max_cycles = deltacchalf_max_cycles
        self.mean_delta_cchalf = []
        self.std_delta_cchalf = []
        self.cchalf_mean = []
        self.n_deleted_datasets = 0
        self.suggested_resolution = None
        super(DialsScale, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def logfile(self):
        return os.path.join(self.workdir, 'dials.scale.log')

    @property
    def expected_output(self):
        return os.path.join(self.workdir, 'scaled.expt')

    @property
    def summary(self):
        return (tuple(self.cchalf_mean), tuple(self.mean_delta_cchalf),
                tuple(self.std_delta_cchalf), self.n_deleted_datasets)

    @property
    def cmd(self):
        return "{dials_exe}.scale {experiments_fname} {reflections_fname} d_min={d_min} " \
               "scaling_options.nproc={nprocs} filtering.method={filtering_method} " \
               "deltacchalf.mode={deltacchalf_mode} deltacchalf.stdcutoff={deltacchalf_stdcutoff} " \
               "deltacchalf.max_cycles={deltacchalf_max_cycles}".format(**self.__dict__).split()

    def _run(self):
        p = subprocess.Popen(self.cmd)
        p.communicate()

    def _parse_logfile(self):
        with open(self.logfile, 'r') as fhandle:
            for line in fhandle:
                if 'CC 1/2 mean:' in line:
                    self.cchalf_mean.append((float(line.rstrip().lstrip().split()[-1])))
                elif 'mean delta_cc_half' in line:
                    self.mean_delta_cchalf.append(float(line.rstrip().lstrip().split()[-1]))
                elif 'stddev delta_cc_half' in line:
                    self.std_delta_cchalf.append(float(line.rstrip().lstrip().split()[-1]))
                elif 'Removed datasets:' in line:
                    self.n_deleted_datasets += len(json.loads(line.split(':')[-1].rstrip().lstrip()))
                elif 'Resolution limit suggested from CC½ fit' in line:
                    self.suggested_resolution = float(line.rstrip().split()[-1])
