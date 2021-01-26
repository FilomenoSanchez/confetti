from confetti.io.parser import Parser
from dials.array_family import flex
from dials.util.phil import FilenameDataWrapper
from dxtbx.model.experiment_list import ExperimentListFactory


class Experiments(Parser):

    def _parse(self):
        self.data = self.read_experiments(self.fname)

    @staticmethod
    def read_experiments(fname):
        wrapper = FilenameDataWrapper(
            filename=fname,
            data=ExperimentListFactory.from_json_file(fname, check_format=True)
        )
        return wrapper.data

    @staticmethod
    def load_templates(experiments):
        return [img_set.get_template() for img_set in experiments.imagesets()]

