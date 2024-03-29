import abc
import os
import logging

ABC = abc.ABCMeta('ABC', (object,), {})


class Wrapper(ABC):
    """Abstract class for wrappers"""

    def __init__(self, workdir):

        self.error = False
        self.workdir = workdir
        self.logger = logging.getLogger(__name__)

    # ------------------ Abstract methods and properties ------------------

    @abc.abstractmethod
    def _run(self):
        """Abstract method to run the wrapper"""
        pass

    @abc.abstractmethod
    def _parse_logfile(self):
        """Abstract method to parse the log file of the wrapper"""
        pass

    @property
    @abc.abstractmethod
    def keywords(self):
        """Abstract property to store the keywords to use in the wrapper"""
        pass

    @property
    @abc.abstractmethod
    def cmd(self):
        """Abstract property to store command to run in the terminal (if any)"""
        pass

    @property
    @abc.abstractmethod
    def expected_output(self):
        """Abstract property to store the expected output file name"""
        pass

    @property
    @abc.abstractmethod
    def logfile(self):
        """Abstract property to store the log file name"""
        pass

    # ------------------ Some general methods ------------------

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)

    def check_output(self):
        if self.expected_output is not None and not os.path.isfile(self.expected_output):
            self.error = True

    def run(self):
        self.make_workdir()
        self._run()
        self.check_output()
        if self.logfile is not None and os.path.isfile(self.logfile):
            self._parse_logfile()
        if 'dials' in logging.Logger.manager.loggerDict.keys():
            logger = logging.getLogger('dials')
            while logger.hasHandlers():
                logger.removeHandler(logger.handlers[0])

