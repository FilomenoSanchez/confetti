from confetti.io.parser import Parser
from dials.array_family import flex
from dials.util.phil import FilenameDataWrapper


class Reflections(Parser):

    def _parse(self):
        self.data = self.read_reflections(self.fname)

    @staticmethod
    def read_reflections(fname):
        wrapper = FilenameDataWrapper(filename=fname, data=flex.reflection_table.from_file(fname))
        return wrapper.data

