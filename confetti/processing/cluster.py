import os
import logging
import confetti.wrappers
from cached_property import cached_property


class Cluster(object):

    def __init__(self, id, workdir, sweeps_dir, clustering_threshold=5000, nprocs=1):
        self.id = id
        self.workdir = os.path.join(workdir, 'cluster_{}'.format(id))
        self.error = False
        self.nprocs = nprocs
        self.clustering_threshold = clustering_threshold
        self.logger = logging.getLogger(__name__)
        self.sweeps_dir = sweeps_dir
        self.experiments_identifiers = []
        self.nclusters = 'NA'
        self.resolution = 'NA'
        self.scaling_stats = ['NA', 'NA', 'NA', 'NA']
        self.merging_stats = ['NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA']
        self.exclude_sweeps = []

    # ------------------ General properties ------------------

    @property
    def hklout(self):
        return os.path.join(self.workdir, 'merged_FREE.mtz')

    @property
    def scaled_refl(self):
        return os.path.join(self.workdir, 'scaled.refl')

    @property
    def scaled_expt(self):
        return os.path.join(self.workdir, 'scaled.expt')

    @property
    def summary(self):
        return (self.id, self.clustering_threshold, self.nclusters, self.workdir, self.hklout,
                self.scaled_refl, self.scaled_expt, self.resolution, *self.scaling_stats,
                *self.merging_stats, tuple(sorted(self.experiments_identifiers)))

    @cached_property
    def input_fnames(self):

        expt_list = []
        refl_list = []

        for sweep_dir in os.listdir(self.sweeps_dir):
            if sweep_dir in self.exclude_sweeps:
                continue
            reflections_fname = os.path.join(self.sweeps_dir, sweep_dir, 'integrated.refl')
            experiments_fname = os.path.join(self.sweeps_dir, sweep_dir, 'integrated.expt')

            if os.path.isfile(reflections_fname) and os.path.isfile(experiments_fname):
                expt_list.append(experiments_fname)
                refl_list.append(reflections_fname)

        return ' '.join(sorted(expt_list) + sorted(refl_list))

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    # ------------------ General Methods ------------------

    def process(self):
        self.make_workdir()
        os.chdir(self.workdir)

        dials_cosym = confetti.wrappers.DialsCosym(self.workdir, self.input_fnames,
                                                   self.clustering_threshold, self.nprocs)
        dials_cosym.run()
        self.experiments_identifiers = dials_cosym.cluster_experiment_identifiers
        self.nclusters = dials_cosym.nclusters
        if dials_cosym.error:
            self.logger.error('Cluster_{} failed to run cosym'.format(self.id))
            self.error = True
            return
        elif dials_cosym.nclusters < 1 or len(dials_cosym.cluster_experiment_identifiers) <= 1:
            self.logger.warning('Cluster_{} found no clusters!'.format(self.id))
            self.error = True
            return

        dials_resolution = confetti.wrappers.DialsEstimateResolution(self.workdir)
        dials_resolution.run()
        if dials_resolution.error:
            self.logger.error('Cluster_{} failed to estimate resolution'.format(self.id))
            self.error = True
            return

        self.resolution = dials_resolution.resolution
        dials_scale = self.scale()
        if dials_scale.error:
            self.logger.error('Cluster_{} failed to scale'.format(self.id))
            self.error = True
            return

        if self.resolution is None and dials_scale.suggested_resolution is not None:
            self.resolution = dials_scale.suggested_resolution
            dials_scale = self.scale()
            if dials_scale.error:
                self.logger.error('Cluster_{} failed to re-scale to resolution {}'.format(self.id, self.resolution))
                self.error = True
                return

        self.scaling_stats = dials_scale.summary

        dials_merge = confetti.wrappers.DialsMerge(self.workdir)
        dials_merge.run()
        if dials_merge.error:
            self.logger.error('Cluster_{} failed to merge'.format(self.id))
            self.error = True
            return
        self.merging_stats = dials_merge.summary

        freerflag = confetti.wrappers.FreeRFlag(self.workdir, 'merged.mtz', 'merged_FREE.mtz')
        freerflag.run()
        if freerflag.error:
            self.logger.error('Cluster_{} failed to create FREE flag'.format(self.id))
            self.error = True
            return

    def scale(self):
        dials_scale = confetti.wrappers.DialsScale(self.workdir, self.resolution, self.nprocs)
        dials_scale.run()
        return dials_scale
