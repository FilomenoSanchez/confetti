from confetti.io.parser import Parser
from dials.array_family import flex
from dials.util.phil import FilenameDataWrapper
from dxtbx.model.experiment_list import ExperimentListFactory


class Experiments(Parser):

    def _parse(self):
        self.data = self.read_experiments(self.fname)

        self.templates = []
        for imageset in self.data.imagesets():
            self.templates.append(imageset.get_template())

        self.imagesets = []
        for imageset in self.data.imagesets():
            self.imagesets.append(imageset.paths())

        self.identifiers = []
        for experiment in self.data:
            self.identifiers.append(experiment.identifier)

    @staticmethod
    def read_experiments(fname):
        wrapper = FilenameDataWrapper(
            filename=fname,
            data=ExperimentListFactory.from_json_file(fname, check_format=True)
        )
        return wrapper.data
