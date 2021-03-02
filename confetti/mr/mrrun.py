import os
import pickle
import pyjob
import logging
from confetti.mr import MtzParser
from confetti.wrappers import Phaser, Refmac, Buccaneer, Shelxe


class MrRun(object):

    def __init__(self, id, workdir, mtz_fname, mw, phaser_stdin, refmac_stdin, buccaneer_keywords, shelxe_keywords):
        self.id = id
        self.mtz_fname = mtz_fname
        self.workdir = os.path.join(workdir, 'mrrun_{}'.format(id))
        self.pickle_fname = os.path.join(self.workdir, 'mrrun.pckl')
        self.mw = mw
        self.ncopies = 0
        self.solvent = 0
        self.nreflections = 0
        self.phaser_stdin = phaser_stdin
        self.phaser = None
        self.refmac_stdin = refmac_stdin
        self.refmac = None
        self.buccaneer_keywords = buccaneer_keywords
        self.buccaneer = None
        self.shelxe_keywords = shelxe_keywords
        self.shelxe = None
        self.initiate_wrappers()
        self.dials_exe = 'dials'
        self.logger = logging.getLogger(__name__)

    # ------------------ Class methods ------------------

    @classmethod
    def from_pickle(cls, pickle_fname):
        with open(pickle_fname, 'rb') as fhandle:
            return pickle.load(fhandle)

    # ------------------ General properties ------------------

    @property
    def python_script(self):
        return """{dials_exe}.python << EOF
from confetti.mr import MrRun
mr_run = MrRun(1, '{workdir}', '{mtz_fname}', {mw}, 'a', 'b', 'c', 'd').from_pickle('{pickle_fname}')
mr_run.run()
mr_run.dump_pickle()
EOF""".format(**self.__dict__)

    @property
    def script(self):
        script = pyjob.Script(directory=self.workdir, prefix='mrrun_{}'.format(self.id), stem='', suffix='.sh')
        script.append(self.python_script)
        return script

    @property
    def summary(self):
        return *self.phaser.summary, *self.refmac.summary, *self.shelxe.summary, *self.buccaneer.summary

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

        self.phaser.run()
        if self.phaser.error:
            self.logger.error('MR-Run {} failed to execute phaser'.format(self.id))
            return

        self.refmac.run()
        if self.refmac.error:
            self.logger.error('MR-Run {} failed to execute refmac'.format(self.id))
            return

        self.buccaneer.run()
        if self.buccaneer.error:
            self.logger.error('MR-Run {} failed to execute buccaneer'.format(self.id))

        self.shelxe.run()
        if self.shelxe.error:
            self.logger.error('MR-Run {} failed to execute shelxe'.format(self.id))

    def initiate_wrappers(self):
        self.estimate_contents()
        self.phaser = Phaser(self.workdir, self.ncopies, self.mw, self.mtz_fname, self.phaser_stdin)
        self.refmac = Refmac(self.workdir, self.mtz_fname, self.phaser.expected_output, self.refmac_stdin)
        self.shelxe = Shelxe(self.workdir, self.refmac.xyzout, self.mtz_fname, self.solvent, self.nreflections,
                             self.shelxe_keywords)
        self.buccaneer = Buccaneer(self.workdir, self.mtz_fname, self.refmac.hklout, self.refmac.xyzout,
                                   self.buccaneer_keywords)

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
        self.nreflections = mtz_parser.nreflections
