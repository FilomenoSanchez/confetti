import os
from confetti.mr import MtzParser


class MrRun(object):

    def __init__(self, id, workdir, mtz_fname, mw, phaser_stdin, refmac_stdin, buccaneer_stdin):
        self.id = id
        self.mtz_fname = mtz_fname
        self.workdir = os.path.join(workdir, 'mr_{}'.format(id))
        self.phaser_stdin = phaser_stdin
        self.refmac_stdin = refmac_stdin
        self.buccaneer_stdin = buccaneer_stdin
        self.mw = mw
        self.mtz_parser = MtzParser(self.mtz_fname)
        self.mtz_parser.parse()
        self.ncopies, self.solvent = self.estimate_contents(self.mtz_parser.reflection_file.cell.volume_per_image(), mw)

    @staticmethod
    def estimate_contents(cell_volume, mw):

        for ncopies in [1, 2, 3, 4, 5]:

            matthews = cell_volume / (mw * ncopies)
            protein_fraction = 1. / (6.02214e23 * 1e-24 * 1.35 * matthews)
            solvent = round((1 - protein_fraction), 1)

            if round(matthews, 3) <= 3.59:
                break

        if solvent <= 0.4 and ncopies != 1:
            ncopies -= 1
            matthews = cell_volume / (mw * ncopies)
            protein_fraction = 1. / (6.02214e23 * 1e-24 * 1.35 * matthews)
            solvent = round((1 - protein_fraction), 1)

        return ncopies, solvent
