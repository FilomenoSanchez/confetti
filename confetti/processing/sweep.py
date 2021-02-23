import os
import pyjob
import pickle
import logging
from cached_property import cached_property
from confetti.io import Experiments


class Sweep(object):

    def __init__(self, id, workdir, image_fnames):
        self.id = id
        self.image_fnames = image_fnames
        self.workdir = os.path.join(workdir, 'sweep_{}'.format(id))
        self.error = False
        self.dials_exe = 'dials'
        self.logger = logging.getLogger()

    # ------------------ Class methods ------------------

    @classmethod
    def from_pickle(cls, pickle_fname):
        with open(pickle_fname, 'rb') as fhandle:
            return pickle.load(fhandle)

    # ------------------ General properties ------------------

    @property
    def size(self):
        return len(self.image_fnames)

    @property
    def integrated_reflections(self):
        return os.path.join(self.workdir, 'integrated.refl')

    @property
    def integrated_experiments(self):
        return os.path.join(self.workdir, 'integrated.expt')

    @cached_property
    def experiment_identifier(self):
        experiments = Experiments(self.integrated_experiments)
        return experiments[0].identifier

    @property
    def pickle_fname(self):
        return os.path.join(self.workdir, 'sweep.pckl')

    @property
    def python_script(self):
        return """{dials_exe}.python << EOF
from confetti.processing import Sweep
sweep = Sweep('dummy', 'dummy', 'dummy').from_pickle({pickle_fname})
sweep.process()
sweep.dump_pickle()
EOF""".format(**self.__dict__)

    @property
    def script(self):
        script = pyjob.Script(directory=self.workdir, prefix='sweep_'.format(self.id.lower()), stem='', suffix='.sh')
        script.append(self.python_script)
        return script

    # ------------------ General methods ------------------

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def dump_pickle(self):
        self.make_workdir()
        with open(self.pickle_fname, 'wb') as fhandle:
            pickle.dump(self, fhandle)

    def process(self):
        self.make_workdir()
        os.chdir(self.workdir)

        # Import data and find spots
        cmd = '{}.import {}'.format(self.dials_exe, self.image_fnames).split()
        pyjob.cexec(cmd)
        cmd = 'dials.find_spots imported.expt'.split()
        pyjob.cexec(cmd)

        # Indexing in P1
        cmd = "{}.index imported.expt strong.refl".format(self.dials_exe).split()
        pyjob.cexec(cmd)
        if not os.path.isfile("P1_models.expt"):
            self.logger.error("Sweep {} failed in initial indexing".format(self.id))
            self.error = True
            return

        # Model refinement
        cmd = "{}.refine indexed.expt indexed.refl scan_varying=false " \
              "outlier.algorithm=tukey".format(self.dials_exe).split()
        pyjob.cexec(cmd)
        if not os.path.isfile("refined.expt"):
            self.logger.error("Sweep {} failed in refinement".format(self.id))
            self.error = True
            return

        # Do not use the result for scaling/merging!
        cmd = "{}.integrate refined.expt indexed.refl".format(self.dials_exe).split()
        pyjob.cexec(cmd)
        if not os.path.isfile("integrated.refl"):
            self.logger.error("Sweep {} failed during integration".format(self.id))
            self.error = True
            return

        # create MTZ
        cmd = "{}.export refined.expt integrated.refl intensity=sum " \
              "mtz.hklout=integrated.mtz".format(self.dials_exe).split()
        pyjob.cexec(cmd)
        if not os.path.isfile("integrated.mtz"):
            self.logger.error("Sweep {} failed during MTZ export".format(self.id))
            self.error = True
            return
