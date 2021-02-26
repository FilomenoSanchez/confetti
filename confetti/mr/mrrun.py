import os
import pickle
import logging
from confetti.mr import MtzParser
from confetti.wrappers import Phaser, Refmac, Buccaneer


class MrRun(object):

    def __init__(self, id, workdir, mtz_fname, mw, phaser_stdin, refmac_stdin, buccaneer_keywords):
        self.id = id
        self.mtz_fname = mtz_fname
        self.workdir = os.path.join(workdir, 'mr_{}'.format(id))
        self.pickle_fname = os.path.join(self.workdir, 'mrrun.pckl')
        self.phaser = None
        self.refmac_stdin = refmac_stdin
        self.refmac = None
        self.buccaneer = None
        self.buccaneer_keywords = buccaneer_keywords
        self.mw = mw
        self.ncopies = 0
        self.solvent = 0
        self.estimate_contents()
        self.phaser_stdin = phaser_stdin.format(**{'COPIES': self.ncopies, 'MW': self.mw, 'HKLIN': self.mtz_fname})
        self.logger = logging.getLogger(__name__)

        # ------------------ Class methods ------------------

    @classmethod
    def from_pickle(cls, pickle_fname):
        with open(pickle_fname, 'rb') as fhandle:
            return pickle.load(fhandle)

    # ------------------ General methods ------------------

    def dump_pickle(self):
        self.make_workdir()
        with open(self.pickle_fname, 'wb') as fhandle:
            pickle.dump(self, fhandle)

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def run(self):
        self.make_workdir()

        self.phaser = Phaser(self.workdir, self.phaser_stdin)
        self.phaser.run()
        if self.phaser.error:
            self.logger.error('MR-Run {} failed to execute phaser'.format(self.id))
            return

        self.refmac = Refmac(self.workdir, self.mtz_fname, 'refmac_out.mtz',
                             self.phaser.expected_output, 'refmac_out.pdb', self.refmac_stdin)
        self.refmac.run()
        if self.refmac.error:
            self.logger.error('MR-Run {} failed to execute refmac'.format(self.id))
            return

        self.buccaneer = Buccaneer(self.workdir, self.buccaneer_keywords)
        self.buccaneer.run()
        if self.buccaneer.error:
            self.logger.error('MR-Run {} failed to execute buccaneer'.format(self.id))
            return

    # ------------------ Static methods ------------------

    def estimate_contents(self):
        mtz_parser = MtzParser(self.mtz_fname)
        mtz_parser.parse()
        cell_volume = mtz_parser.reflection_file.cell.volume_per_image()

        for ncopies in [1, 2, 3, 4, 5]:

            matthews = cell_volume / (self.mw * ncopies)
            protein_fraction = 1. / (6.02214e23 * 1e-24 * 1.35 * matthews)
            solvent = round((1 - protein_fraction), 1)

            if round(matthews, 3) <= 3.59:
                break

        if solvent <= 0.4 and ncopies != 1:
            ncopies -= 1
            matthews = cell_volume / (self.mw * ncopies)
            protein_fraction = 1. / (6.02214e23 * 1e-24 * 1.35 * matthews)
            solvent = round((1 - protein_fraction), 1)

        self.ncopies = ncopies
        self.solvent = solvent
