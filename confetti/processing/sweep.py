import os
import pyjob
import pickle
import logging
from cached_property import cached_property
from confetti.io import Experiments
import confetti.wrappers
from dxtbx.model.experiment_list import ExperimentList


class Sweep(object):

    def __init__(self, id, workdir):
        self.id = id
        self.workdir = os.path.join(workdir, 'sweep_{}'.format(id))
        self.input_experiment_fname = os.path.join(self.workdir, 'imported.expt')
        self.error = False
        self.dials_exe = 'dials'
        self.pickle_fname = os.path.join(self.workdir, 'sweep.pckl')
        self.logger = logging.getLogger(__name__)

    # ------------------ Class methods ------------------

    @classmethod
    def from_pickle(cls, pickle_fname):
        with open(pickle_fname, 'rb') as fhandle:
            return pickle.load(fhandle)

    # ------------------ General properties ------------------

    @property
    def integrated_reflections(self):
        return os.path.join(self.workdir, 'integrated.refl')

    @property
    def integrated_experiments(self):
        return os.path.join(self.workdir, 'integrated.expt')

    @cached_property
    def experiment_identifier(self):
        experiments = Experiments(self.integrated_experiments)
        return experiments.data[0].identifier

    @property
    def python_script(self):
        return """{dials_exe}.python << EOF
from confetti.processing import Sweep
sweep = Sweep('{id}', '{workdir}').from_pickle('{pickle_fname}')
sweep.process()
sweep.dump_pickle()
EOF""".format(**self.__dict__)

    @property
    def script(self):
        script = pyjob.Script(directory=self.workdir, prefix='sweep_{}'.format(self.id), stem='', suffix='.sh')
        script.append(self.python_script)
        return script

    # ------------------ General methods ------------------

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def prepare_input(self, experiment):
        self.make_workdir()
        experiment_list = ExperimentList()
        experiment_list.append(experiment)
        experiment_list.as_file(self.input_experiment_fname)

    def dump_pickle(self):
        self.make_workdir()
        with open(self.pickle_fname, 'wb') as fhandle:
            pickle.dump(self, fhandle)

    def process(self):
        self.make_workdir()
        os.chdir(self.workdir)

        if not os.path.isfile(self.input_experiment_fname):
            self.logger.error('Sweep {} unable to find input file {}'.format(self.id, self.input_experiment_fname))
            self.error = True
            return

        dials_find_spots = confetti.wrappers.DialsFindSpots(self.workdir)
        dials_find_spots.run()
        if dials_find_spots.error:
            self.logger.error('Sweep {} failed trying to find spots'.format(self.id))
            self.error = True
            return

        dials_index = confetti.wrappers.DialsIndex(self.workdir)
        dials_index.run()
        if dials_index.error:
            self.logger.error("Sweep {} failed in initial indexing".format(self.id))
            self.error = True
            return

        dials_refine = confetti.wrappers.DialsRefine(self.workdir)
        dials_refine.run()
        if dials_refine.error:
            self.logger.error("Sweep {} failed in refinement".format(self.id))
            self.error = True
            return

        dials_integrate = confetti.wrappers.DialsIntegrate(self.workdir)
        dials_integrate.run()
        if dials_integrate.error:
            self.logger.error("Sweep {} failed during integration".format(self.id))
            self.error = True
            return

        dials_export = confetti.wrappers.DialsExport(self.workdir)
        dials_export.run()
        if dials_export.error:
            self.logger.error("Sweep {} failed during MTZ export".format(self.id))
            self.error = True
