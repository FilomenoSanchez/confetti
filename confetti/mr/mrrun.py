import os
import pickle
from Bio import SeqIO
from Bio.SeqUtils import molecular_weight
import pyjob
import logging
from confetti.mr import MtzParser, HklImport
from confetti.wrappers import Phaser, Refmac, Buccaneer, Shelxe, Reindex


class MrRun(object):

    def __init__(self, id, workdir, mtz_fname, fasta_fname, searchmodel, phaser_stdin, refmac_stdin,
                 buccaneer_keywords, shelxe_keywords, rms=0.1, num=1, is_fragment=False):
        self.id = id
        self.mtz_fname = mtz_fname
        self.fasta_fname = fasta_fname
        self.workdir = os.path.join(workdir, 'mrrun_{}'.format(id))
        self.pickle_fname = os.path.join(self.workdir, 'mrrun.pckl')
        self.mw = None
        self.searchmodel = searchmodel
        self.rms = rms
        self.num = num
        self.is_fragment = is_fragment
        self.ncopies = 0
        self.solvent = 0
        self.nreflections = 0
        self.low_res = 0
        self.high_res = 0
        self.spacegroup = None
        self.phaser_stdin = phaser_stdin
        self.phaser = None
        self.refmac_stdin = refmac_stdin
        self.refmac = None
        self.buccaneer_keywords = buccaneer_keywords
        self.buccaneer = None
        self.shelxe_keywords = shelxe_keywords
        self.shelxe = None
        self.hklimport = None
        self.dials_exe = 'dials'
        self.error = False
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
mr_run = MrRun(1, '{workdir}', '{mtz_fname}', 'a', 'b', 'c', 'd', 'e', 'f').from_pickle('{pickle_fname}')
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

    # ------------------ Static methods ------------------

    @staticmethod
    def calculate_mw(fname):
        target_chains = [str(chain.seq) for chain in list(SeqIO.parse(fname, "fasta"))]
        target_chains = list(set(target_chains))
        mw = 0.0
        for seq in target_chains:
            seq = seq.replace("X", "A")
            mw += round(molecular_weight(seq, "protein"), 2)

        return mw

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
        self.initiate_wrappers()

        if self.error:
            self.logger.error('MR-Run {} failed to initiate wrappers'.format(self.id))
            return

        self.phaser.run()
        if self.phaser.error:
            self.logger.error('MR-Run {} failed to execute phaser'.format(self.id))
            self.error = True
            return

        if self.phaser.output_spacegroup != self.spacegroup:
            reindexed_error = self.reindex_input(self.phaser.output_spacegroup)
            if reindexed_error:
                self.logger.error('MR-Run {} failed to reindex input'.format(self.id))
                self.error = True
                return

        self.refmac.run()
        if self.refmac.error:
            self.logger.error('MR-Run {} failed to execute refmac'.format(self.id))
            self.error = True
            return

        self.buccaneer.run()
        if self.buccaneer.error:
            self.logger.error('MR-Run {} failed to execute buccaneer'.format(self.id))
            self.error = True

        #self.shelxe.run()
        #if self.shelxe.error:
        #    self.logger.error('MR-Run {} failed to execute shelxe'.format(self.id))
        #    self.error = True

    def initiate_wrappers(self):
        self.mw = self.calculate_mw(self.fasta_fname)
        self.hklimport = HklImport(self.workdir, self.mtz_fname, 'merged_FREE_imported.mtz')
        self.hklimport.run()
        if self.hklimport.error:
            self.error = True
            self.logger.error('MR-Run {} failed to import mtz file'.format(self.id))
            return

        self.estimate_contents()
        self.phaser = Phaser(self.workdir, self.hklimport.hklout, self.ncopies, self.mw,
                             self.searchmodel, self.rms, self.num, self.phaser_stdin)
        self.refmac = Refmac(self.workdir, self.hklimport.hklout, self.phaser.expected_output,
                             self.low_res, self.high_res, self.refmac_stdin)
        self.shelxe = Shelxe(self.workdir, self.refmac.xyzout, self.hklimport.hklout, self.solvent,
                             self.nreflections, self.shelxe_keywords)
        self.buccaneer = Buccaneer(self.workdir, self.hklimport.hklout, self.refmac.hklout,
                                   self.refmac.xyzout, self.fasta_fname, self.solvent, self.buccaneer_keywords,
                                   self.is_fragment)

    def reindex_input(self, spacegroup):
        reindexed_mtz = os.path.join(self.workdir, 'reindex', 'reindex_input_{}.mtz'.format(spacegroup))
        reindex = Reindex(self.workdir, self.hklimport.hklout, reindexed_mtz, spacegroup)
        reindex.run()
        self.estimate_contents(reindexed_mtz)
        self.refmac.hklin = reindexed_mtz
        self.refmac.high_res = self.high_res
        self.refmac.low_res = self.low_res
        self.shelxe.hklin = reindexed_mtz
        self.shelxe.solvent = self.solvent
        self.shelxe.nreflections = self.nreflections
        self.buccaneer.mtz_fname = reindexed_mtz
        return reindex.error

    def estimate_contents(self, hklin=None):
        if hklin is None:
            mtz_parser = MtzParser(self.hklimport.hklout)
        else:
            mtz_parser = MtzParser(hklin)
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
        self.spacegroup = mtz_parser.spacegroup_number
        self.low_res = mtz_parser.reflection_file.resolution_low()
        self.high_res = mtz_parser.reflection_file.resolution_high()
