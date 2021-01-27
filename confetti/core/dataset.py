import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
from scipy.spatial import ConvexHull
from sklearn.cluster import MeanShift
from cctbx import miller
from confetti.io.reflections_parser import Reflections
from confetti.io.experiments_parser import Experiments


class Dataset(object):

    def __init__(self):
        self.table = None
        self.reflections = None
        self.experiments = None

    # ------------------ Class methods ------------------

    @classmethod
    def from_raw_data(cls, experiments_fname, reflections_fname, expand_to_p1=True):
        result = cls()
        result.reflections = Reflections(reflections_fname)
        result.experiments = Experiments(experiments_fname)
        result.get_reflection_table(expand_to_p1)
        return result

    @classmethod
    def from_csv(cls, csv_fname):
        result = cls()
        result.table = pd.read_csv(csv_fname)
        return result

    # ------------------ Static methods ------------------

    @staticmethod
    def get_density(values):
        kde = gaussian_kde(values)
        return kde(values)

    @staticmethod
    def get_spherical_coords(df):
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

    # ------------------ Methods ------------------

    def get_reflection_table(self, expand_to_p1=True):
        miller_array = self.reflections.data.as_miller_array(self.experiments.data[0])
        observed_set = miller_array.unique_under_symmetry().map_to_asu()
        observed_set = observed_set.generate_bijvoet_mates()
        complete_set = observed_set.complete_set()
        missing_set = complete_set.lone_set(observed_set)

        if expand_to_p1:
            missing_set = missing_set.expand_to_p1()
            complete_set = complete_set.expand_to_p1()

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
        r, theta, phi = self.get_spherical_coords(df)
        df['r'] = r
        df['phi'] = phi
        df['theta'] = theta
        self.table = df

    def get_res_density(self):
        self.table['RES_DENSITY'] = self.get_density(self.table['RES'])
        self.table['RES_CUMSUM'] = self.get_cumulative_density(self.table['RES_DENSITY'])

    def get_unique_reflections(self):
        if self.reflections is None:
            print('No reflections provided!')
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

    def get_meanshift_labels(self, bandwidth=0.2, njobs=1):
        X = self.table.loc[(~self.table['OBSERVED']) & (self.table['WEIGHTED_DENSITY'] > 1.5)][['A', 'B', 'C']]
        clustering = MeanShift(bandwidth=bandwidth, n_jobs=njobs).fit(X)
        labels = []
        idx = 0
        for is_observed, abc_density in zip(self.table['OBSERVED'].to_list(), self.table['WEIGHTED_DENSITY'].to_list()):
            if abc_density > 1.5 and not is_observed:
                labels.append(clustering.labels_[idx])
                idx += 1
            else:
                labels.append(np.nan)

        self.table['MEANSHIFT_LABELS'] = labels

    def get_cluster_hull(self, cluster_label):
        tmp_df = self.table[self.table['MEANSHIFT_LABELS'] == cluster_label][['A', 'B', 'C']]
        tmp_df.reset_index(drop=True, inplace=True)
        hull = ConvexHull(tmp_df)
        return hull
