import os
import logging
import confetti.wrappers


class Cluster(object):

    def __init__(self, id, workdir, sweeps_dir, clustering_threshold=5000, nprocs=1):
        self.id = id
        self.workdir = os.path.join(workdir, 'cluster_{}'.format(id))
        self.error = False
        self.nprocs = nprocs
        self.clustering_threshold = clustering_threshold
        self.dials_exe = 'dials'
        self.logger = logging.getLogger(__name__)
        self.sweeps_dir = sweeps_dir
        self.experiments_identifiers = None

    @property
    def hklout(self):
        return os.path.join(self.workdir, 'merged_FREE.mtz')

    @property
    def input_fnames(self):
        return os.path.join(self.sweeps_dir, 'sweep_*', 'integrated*')

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def process(self):
        self.make_workdir()
        os.chdir(self.workdir)

        dials_cosym = confetti.wrappers.DialsCosym(self.workdir, self.input_fnames, self.dials_exe,
                                                   self.clustering_threshold, self.nprocs)
        dials_cosym.run()
        if dials_cosym.error:
            self.logger.error('Cluster {} failed to run cosym'.format(self.id))
            self.error = True
            return
        self.experiments_identifiers = dials_cosym.cluster_experiment_identifiers
        self.nlusters = dials_cosym.nclusters

        dials_resolution = confetti.wrappers.DialsEstimateResolution(self.workdir, 'symmetrized.*', self.dials_exe)
        dials_resolution.run()
        if dials_resolution.error:
            self.logger.error('Cluster {} failed to estimate resolution'.format(self.id))
            self.error = True
            return

        dials_scale = confetti.wrappers.DialsScale(self.workdir, 'symmetrized.refl', 'symmetrized.expt',
                                                   dials_resolution.resolution, self.dials_exe, self.nprocs)
        dials_scale.run()
        if dials_scale.error:
            self.logger.error('Cluster {} failed to scale'.format(self.id))
            self.error = True
            return

        dials_merge = confetti.wrappers.DialsMerge(self.workdir, 'scaled.*', self.dials_exe)
        dials_merge.run()
        if dials_merge.error:
            self.logger.error('Cluster {} failed to merge'.format(self.id))
            self.error = True
            return

        freerflag = confetti.wrappers.FreeRFlag(self.workdir, 'merged.mtz', 'merged_FREE.mtz')
        freerflag.run()
        if freerflag.error:
            self.logger.error('Cluster {} failed to create FREE flag'.format(self.id))
            self.error = True
            return
