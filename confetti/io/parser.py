import abc
import os
import logging

ABC = abc.ABCMeta('ABC', (object,), {})


class Parser(ABC):

    def __init__(self, fname):
        self.fname = fname
        self.error = False
        self.data = None
        self.logger = logging.getLogger(__name__)
        self.parse()

    @abc.abstractmethod
    def _parse(self):
        pass

    def parse(self):
        self.check_input()
        if not self.error:
            self._parse()

    def check_input(self):
        """Check if :py:attr:`~confetti.io.parsers.parser.fname` exists"""

        if self.fname is not None and not os.path.isfile(self.fname):
            self.error = True
            self.logger.error('Cannot find input file, please make sure it exists: %s' % self.fname)
