import pandas as pd
import numpy as np
import pyjob
import logging
from scipy.stats import gaussian_kde, ks_2samp
from scipy.spatial import ConvexHull
from scipy.spatial.qhull import QhullError
from sklearn.cluster import MeanShift
from cctbx import miller, array_family
from confetti.io.reflections_parser import Reflections
from confetti.io.experiments_parser import Experiments


class Completeness(object):

    def __init__(self):
        self.is_p1 = False
        self.table = None
        self.reflections = None
        self.experiments = None
        self.reflections_fname = None
        self.experiments_fname = None
        self.csv_out_fname = None
        self.dials_exe = 'dials'
        self.workdir = None
        self.id = None
        self.logger = logging.getLogger(__name__)

    # ------------------ Class methods ------------------

    @classmethod
    def from_raw_data(cls, experiments_fname, reflections_fname, expand_to_p1=True):
        dataset = cls()
        dataset.register_raw_data(experiments_fname, reflections_fname)
        dataset.get_reflection_table(expand_to_p1)
        return dataset

    @classmethod
    def from_csv(cls, csv_fname, is_p1=True):
        dataset = cls()
        dataset.table = pd.read_csv(csv_fname)
        if 'Unnamed: 0' in dataset.table.columns:
            dataset.table.drop('Unnamed: 0', 1, inplace=True)
        dataset.is_p1 = is_p1
        return dataset

    # ------------------ Properties ------------------

    @property
    def python_script(self):
        return """{dials_exe}.python << EOF
from confetti.completeness import Completeness
completeness = Completeness().from_raw_data('{experiments_fname}', '{reflections_fname}', {is_p1})
completeness.get_res_density()
completeness.get_missing_observed_density_abc_weighted('RES_CUMSUM')
completeness.get_meanshift_labels()
completeness.get_unique_reflections()
completeness.table.to_csv('{csv_out_fname}')
EOF""".format(**self.__dict__)

    @property
    def script(self):
        script = pyjob.Script(directory=self.workdir, prefix='completeness_table_{}'.format(self.id),
                              stem='', suffix='.sh')
        script.append(self.python_script)
        return script

    @property
    def completeness(self):

        miller_array = self.reflections.data.as_miller_array(self.experiments.data[0])
        observed_set = miller_array.unique_under_symmetry().map_to_asu()
        observed_set = observed_set.generate_bijvoet_mates()
        self.logger.info('Overall completeness: {}'.format(observed_set.completeness()))

        self.logger.info('Completeness by bins:')
        binner = observed_set.setup_binner(auto_binning=True)
        completeness = observed_set.completeness(use_binning=True)
        for bin_idx, bin_completeness in zip(binner.range_all(), completeness.data):
            self.logger.info(bin_idx, binner.bin_d_range(bin_idx), bin_completeness)

        return observed_set.completeness()

    @property
    def ksd_r(self):
        ks = ks_2samp(self.table.r, self.table.loc[self.table.OBSERVED].r)
        return ks.statistic

    @property
    def ksd_r_prime(self):
        ks = ks_2samp(np.cumsum(self.table['RES'].sort_values(ascending=True)),
                      np.cumsum(self.table.loc[(self.table.OBSERVED)]['RES'].sort_values(ascending=True)))
        return ks.statistic

    @property
    def ksd_theta(self):
        ks = ks_2samp(self.table.theta, self.table.loc[self.table.OBSERVED].theta)
        return ks.statistic

    @property
    def ksd_phi(self):
        ks = ks_2samp(self.table.phi, self.table.loc[self.table.OBSERVED].phi)
        return ks.statistic

    @property
    def symmetry_level(self):
        if self.table is None or 'IS_UNIQUE' not in self.table.columns:
            return None
        return self.table.shape[0] / self.table.loc[self.table.IS_UNIQUE].shape[0]

    @property
    def summary(self):
        return (self.is_p1, self.symmetry_level, self.reflections_fname, self.experiments_fname, self.ksd_r,
                self.ksd_phi, self.ksd_theta, self.ksd_r_prime, self.get_ratio_high_density_reflections(),
                self.get_ratio_high_density_reflections(0.6), self.get_ratio_high_density_reflections(0.9),
                self.get_volume_ratio())

    # ------------------ Static methods ------------------

    @staticmethod
    def get_density(values):
        kde = gaussian_kde(values)
        return kde(values)

    @staticmethod
    def compute_spherical_coords(df):
        xyz = df[['A', 'B', 'C']]
        ptsnew = np.hstack((xyz, np.zeros(xyz.shape)))
        xy = xyz['A'] ** 2 + xyz['B'] ** 2
        ptsnew[:, 3] = np.sqrt(xy + xyz['C'] ** 2)
        ptsnew[:, 4] = np.arctan2(np.sqrt(xy), xyz['C'])  # for elevation angle defined from Z-axis down
        # ptsnew[:,4] = np.arctan2(xyz[:,2], np.sqrt(xy)) # for elevation angle defined from XY-plane up
        ptsnew[:, 5] = np.arctan2(xyz['B'], xyz['A'])
        r = ptsnew[:, 3]
        theta = ptsnew[:, 4]
        phi = ptsnew[:, 5]
        return r, theta, phi

    @staticmethod
    def get_cumulative_density(density):
        cumsum = np.cumsum(density)[::-1]
        cumsum.reset_index(drop=True, inplace=True)
        return cumsum

    @staticmethod
    def get_density_abc_weighted(df, weigth):
        tmp_df = df[['A', 'B', 'C']]
        values = tmp_df.T
        kde = gaussian_kde(values, weights=df[weigth])
        return kde(values)

    @staticmethod
    def compute_df(reflections, experiments, expand_to_p1=True):

        miller_array = reflections.as_miller_array(experiments[0])
        observed_set = miller_array.unique_under_symmetry().map_to_asu()

        if expand_to_p1:
            observed_set = observed_set.generate_bijvoet_mates()
            complete_set = observed_set.complete_set()
            missing_set = complete_set.lone_set(observed_set)
            missing_set = missing_set.expand_to_p1()
            complete_set = complete_set.expand_to_p1()

        else:
            complete_set = observed_set.complete_set()
            missing_set = complete_set.lone_set(observed_set)

        uc = complete_set.unit_cell()
        complete_set_d_spacings = complete_set.d_spacings()

        df = []
        missing_indices = set(missing_set.indices())
        for idx in complete_set_d_spacings:
            rlp = uc.reciprocal_space_vector(idx[0])
            if (idx[0][0], idx[0][1], idx[0][2]) in missing_indices:
                row = [idx[0][0], idx[0][1], idx[0][2], rlp[0], rlp[1], rlp[2], idx[1], False]
            else:
                row = [idx[0][0], idx[0][1], idx[0][2], rlp[0], rlp[1], rlp[2], idx[1], True]

            df.append(row)

        df = pd.DataFrame(df)
        df.columns = ['H', 'K', 'L', 'A', 'B', 'C', 'RES', 'OBSERVED']
        df.sort_values(by='RES', inplace=True, ascending=False)
        df.reset_index(drop=True, inplace=True)
        return df

    # ------------------ Methods ------------------

    def register_raw_data(self, experiments_fname, reflections_fname, update_table=False):
        self.experiments_fname = experiments_fname
        self.experiments = Experiments(experiments_fname)
        self.reflections_fname = reflections_fname
        self.reflections = Reflections(reflections_fname)

        if update_table:
            self.update_table()

    def update_table(self):
        new_df = self.compute_df(self.reflections.data, self.experiments.data, expand_to_p1=self.is_p1)
        observed_indices = set(new_df.loc[new_df.OBSERVED][['H', 'K', 'L']].to_records(index=False).tolist())
        self.table['OBSERVED'] = [True if (h, k, l) in observed_indices else False
                                  for h, k, l in zip(self.table.H, self.table.K, self.table.L)]

    def get_reflection_table(self, expand_to_p1=True):
        if self.reflections is None:
            self.logger.error('No reflections registered!')
            return

        self.logger.info('Creating reflection table')
        df = self.compute_df(self.reflections.data, self.experiments.data, expand_to_p1)
        self.logger.info('Loading spherical coords')
        r, theta, phi = self.compute_spherical_coords(df)
        df['r'] = r
        df['phi'] = phi
        df['theta'] = theta
        self.table = df
        self.is_p1 = expand_to_p1

    def get_res_density(self):
        self.logger.info('Calculating resolution density')
        self.table['RES_DENSITY'] = self.get_density(self.table['RES'])
        self.table['RES_CUMSUM'] = self.get_cumulative_density(self.table['RES_DENSITY'])

    def get_unique_reflections(self):
        if self.reflections is None:
            self.logger.error('No reflections registered!')
            return

        miller_array = self.reflections.data.as_miller_array(self.experiments.data[0])
        space_group = miller_array.space_group()
        miller_unique = miller_array.unique_under_symmetry()

        unique_idx = set(miller_unique.map_to_asu().complete_set().indices())
        bijvoet_idx = set(miller_unique.generate_bijvoet_mates().map_to_asu().complete_set().indices())
        all_indices = [(h, k, l) for h, k, l in zip(self.table.H, self.table.K, self.table.L)]
        is_bijvoet = []
        is_unique = []
        unique_dict = {}

        for idx, index in enumerate(all_indices):
            if index in bijvoet_idx:
                is_bijvoet.append(True)
            else:
                is_bijvoet.append(False)
            if index in unique_idx:
                is_unique.append(True)
                equiv_indices = [equiv.mate().hr() for equiv in miller.sym_equiv_indices(space_group, index).indices()]
                equiv_indices += [equiv.mate().h() for equiv in miller.sym_equiv_indices(space_group, index).indices()]
                for equiv in equiv_indices:
                    unique_dict[equiv] = idx
            else:
                is_unique.append(False)
        unique_ids = [unique_dict[(h, k, l)] for h, k, l in zip(self.table.H, self.table.K, self.table.L)]

        self.table['IS_UNIQUE'] = is_unique
        self.table['IS_BIJVOET'] = is_bijvoet
        self.table['UNIQUE_ID'] = unique_ids

    def get_missing_observed_density_abc_weighted(self, weight):
        self.logger.info('Calculating missing reflection ABC weighted density')

        obs_df = self.table[self.table['OBSERVED']]
        missing_df = self.table[~self.table['OBSERVED']]
        observed_density = self.get_density_abc_weighted(obs_df, weight)
        missing_density = self.get_density_abc_weighted(missing_df, weight)
        observed_idx = 0
        missing_idx = 0
        result = []
        for is_observed in self.table['OBSERVED'].to_list():
            if is_observed:
                result.append(observed_density[observed_idx])
                observed_idx += 1
            else:
                result.append(missing_density[missing_idx])
                missing_idx += 1

        self.table['WEIGHTED_DENSITY'] = result
        norm_density = (self.table.WEIGHTED_DENSITY - self.table.WEIGHTED_DENSITY.min()) / \
                       (self.table.WEIGHTED_DENSITY.max() - self.table.WEIGHTED_DENSITY.min())
        self.table['NORM_WEIGHTED_DENSITY'] = norm_density

    def get_ratio_high_density_reflections(self, threshold=0.3):
        return self.table.loc[(~self.table.OBSERVED) & (self.table.NORM_WEIGHTED_DENSITY > threshold)].shape[0] / \
               self.table.loc[(~self.table.OBSERVED)].shape[0]

    def get_meanshift_labels(self, bandwidth=0.05, njobs=1, threshold_quantile=0.75):
        threshold = self.table.loc[(~self.table.OBSERVED)]['WEIGHTED_DENSITY'].quantile(threshold_quantile)
        X = self.table.loc[(~self.table['OBSERVED']) & (self.table['WEIGHTED_DENSITY'] > threshold)][['A', 'B', 'C']]
        clustering = MeanShift(bandwidth=bandwidth, n_jobs=njobs).fit(X)
        labels = []
        idx = 0
        for is_observed, abc_density in zip(self.table['OBSERVED'].to_list(), self.table['WEIGHTED_DENSITY'].to_list()):
            if abc_density > threshold and not is_observed:
                labels.append(clustering.labels_[idx])
                idx += 1
            else:
                labels.append(np.nan)

        self.table['MEANSHIFT_LABELS'] = labels

    def get_cluster_hull_volume(self, cluster_label):
        tmp_df = self.table[self.table['MEANSHIFT_LABELS'] == cluster_label][['A', 'B', 'C']]
        try:
            tmp_df.reset_index(drop=True, inplace=True)
            hull = ConvexHull(tmp_df)
            return hull.volume
        except QhullError:
            return 0

    def get_volume_ratio(self):
        if 'MEANSHIFT_LABELS' not in self.table.columns:
            self.get_meanshift_labels()

        labels = tuple([x for x in self.table['MEANSHIFT_LABELS'].unique() if pd.notna(x)])

        total_hull = ConvexHull(self.table[['A', 'B', 'C']])
        missing_volume = 0
        for clst_label in labels:
            hull_volume = self.get_cluster_hull_volume(clst_label)
            missing_volume += hull_volume

        return missing_volume / total_hull.volume

    def remove_random_sample(self, sample=0.1):
        if self.reflections is None:
            self.logger.error('No reflections registered!')
            return

        miller_array = self.reflections.data.as_miller_array(self.experiments.data[0])
        space_group = miller_array.space_group()
        delete_nreflections = round(self.table.loc[(self.table.IS_UNIQUE)].shape[0] * sample)
        self.logger.info('Deleting {} reflections at random'.format(delete_nreflections))
        df_to_delete = self.table.sample(n=delete_nreflections, axis=0)

        idx_delete = []
        for h, k, l in zip(df_to_delete.H, df_to_delete.K, df_to_delete.L):
            idx_delete += [equiv.mate().hr() for equiv in miller.sym_equiv_indices(space_group, (h, k, l)).indices()]
            idx_delete += [equiv.mate().h() for equiv in miller.sym_equiv_indices(space_group, (h, k, l)).indices()]
        idx_delete = set(idx_delete)

        array_delete = [1 if idx in idx_delete else 0 for idx in self.reflections.data['miller_index']]
        array_delete = array_family.flex.int(array_delete)
        self.reflections.data['to_delete'] = array_delete
        sel = self.reflections.data['to_delete'] == 1
        self.reflections.data.del_selected(sel)
        del self.reflections.data['to_delete']

        self.update_table()

    def remove_coord_range(self, sample=0.1, coord='phi'):
        if self.reflections is None:
            self.logger.error('No reflections registered!')
            return

        miller_array = self.reflections.data.as_miller_array(self.experiments.data[0])
        space_group = miller_array.space_group()
        nreflections = round(self.table.loc[(self.table.IS_UNIQUE)].shape[0] * sample)
        coord_threshold = self.table.loc[(self.table.IS_UNIQUE)].sort_values(by=coord)[coord].to_list()[nreflections]
        self.logger.info('Deleting {} reflections below {} {}'.format(nreflections, coord, coord_threshold))
        df_to_delete = self.table.loc[(self.table[coord] < coord_threshold) & (self.table.IS_UNIQUE)]

        idx_delete = []
        for h, k, l in zip(df_to_delete.H, df_to_delete.K, df_to_delete.L):
            idx_delete += [equiv.mate().hr() for equiv in miller.sym_equiv_indices(space_group, (h, k, l)).indices()]
            idx_delete += [equiv.mate().h() for equiv in miller.sym_equiv_indices(space_group, (h, k, l)).indices()]
        idx_delete = set(idx_delete)

        array_delete = [1 if idx in idx_delete else 0 for idx in self.reflections.data['miller_index']]
        array_delete = array_family.flex.int(array_delete)
        self.reflections.data['to_delete'] = array_delete
        sel = self.reflections.data['to_delete'] == 1
        self.reflections.data.del_selected(sel)
        del self.reflections.data['to_delete']

        self.update_table()

    def remove_coord_chunks(self, sample=0.1, coord='phi', nchunks=2):
        miller_array = self.reflections.data.as_miller_array(self.experiments.data[0])
        space_group = miller_array.space_group()
        chunk_size = round(self.table.loc[(self.table.IS_UNIQUE)].shape[0] * sample / nchunks)
        self.logger.info('Deleting {} chunks of {} reflections each'.format(nchunks, chunk_size))
        df_sorted = self.table.loc[(self.table.IS_UNIQUE)].sort_values(by=coord)

        df_to_delete = []
        for chunk_idx in range(nchunks):
            start = chunk_idx * (round(len(df_sorted) / nchunks))
            stop = (chunk_idx + 1) * (round(len(df_sorted) / nchunks))
            tmp_df = df_sorted.iloc[start:stop]
            random_start = np.random.randint(tmp_df.shape[0] - chunk_size + 1)
            df_to_delete.append(tmp_df.iloc[random_start:random_start + chunk_size])

        df_to_delete = pd.concat(df_to_delete)

        idx_delete = []
        for h, k, l in zip(df_to_delete.H, df_to_delete.K, df_to_delete.L):
            idx_delete += [equiv.mate().hr() for equiv in miller.sym_equiv_indices(space_group, (h, k, l)).indices()]
            idx_delete += [equiv.mate().h() for equiv in miller.sym_equiv_indices(space_group, (h, k, l)).indices()]
        idx_delete = set(idx_delete)

        array_delete = [1 if idx in idx_delete else 0 for idx in self.reflections.data['miller_index']]
        array_delete = array_family.flex.int(array_delete)
        self.reflections.data['to_delete'] = array_delete
        sel = self.reflections.data['to_delete'] == 1
        self.reflections.data.del_selected(sel)
        del self.reflections.data['to_delete']

        self.update_table()
