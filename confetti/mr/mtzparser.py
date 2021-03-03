import re
import gemmi
from enum import Enum


class MtzColumnLabels(Enum):
    """An enumerator that contains the regular expression used to detect the column labels of a given MTZ file"""
    free = re.compile(r"^.*?[Ff][Rr][Ee][Ee].*")
    i = re.compile(r"^[Ii]")
    sigi = re.compile(r"^[Ss][Ii][Gg][Ii]")
    f = re.compile(r"^[Ff][Pp]?(?![Cc])(?![Ww][Tw])")
    sigf = re.compile(r"^[Ss][Ii][Gg][Ff][Pp]?")
    dp = re.compile(r"^([Dd][Pp]|[Dd][Aa][Nn][Oo][Pp]?)")
    sigdp = re.compile(r"^[Ss][Ii][Gg]([Dd][Pp]|[Dd][Aa][Nn][Oo][Pp]?)")
    i_plus = re.compile(r"^[Ii].*(\(\+\)|[Pp][Ll][Uu][Ss])")
    sigi_plus = re.compile(r"^[Ss][Ii][Gg][Ii].*(\(\+\)|[Pp][Ll][Uu][Ss])")
    f_plus = re.compile(r"^[Ff][Pp]?.*(\(\+\)|[Pp][Ll][Uu][Ss])")
    sigf_plus = re.compile(r"^[Ss][Ii][Gg][Ff][Pp]?.*(\(\+\)|[Pp][Ll][Uu][Ss])")
    i_minus = re.compile(r"^[Ii].*(\(-\)|[Mm][Ii][Nn][Uu][Ss])")
    sigi_minus = re.compile(r"^[Ss][Ii][Gg][Ii].*(\(-\)|[Mm][Ii][Nn][Uu][Ss])")
    f_minus = re.compile(r"^[Ff][Pp]?.*(\(-\)|[Mm][Ii][Nn][Uu][Ss])")
    sigf_minus = re.compile(r"^[Ss][Ii][Gg][Ff][Pp]?.*(\(-\)|[Mm][Ii][Nn][Uu][Ss])")


class MTZColumnTypes(Enum):
    """An enumerator that contains the different types expected for each column of a given MTZ file"""

    free = 'I'
    i = 'J'
    sigi = 'Q'
    f = 'F'
    sigf = 'Q'
    dp = 'D'
    sigdp = 'Q'
    i_plus = 'K'
    sigi_plus = 'M'
    f_plus = 'G'
    sigf_plus = 'L'
    i_minus = 'K'
    sigi_minus = 'M'
    f_minus = 'G'
    sigf_minus = 'L'


class MtzParser(object):

    def __init__(self, fname):
        self.fname = fname
        self.reflection_file = None
        self.f = None
        self.sigf = None
        self.dp = None
        self.sigdp = None
        self.i = None
        self.sigi = None
        self.free = None
        self.f_plus = None
        self.sigf_plus = None
        self.i_plus = None
        self.sigi_plus = None
        self.f_minus = None
        self.sigf_minus = None
        self.i_minus = None
        self.sigi_minus = None
        self.resolution = None
        self.nreflections = None
        self.spacegroup_symbol = None
        self.spacegroup_number = None
        self.read_reflections()

    def read_reflections(self):
        self.reflection_file = gemmi.read_mtz_file(self.fname)
        self.nreflections = self.reflection_file.nreflections
        self.spacegroup_symbol = self.reflection_file.spacegroup.hm
        self.spacegroup_number = self.reflection_file.spacegroup.number
        self.resolution = self.reflection_file.resolution_high()

    def parse(self):
        for label in MtzColumnLabels:
            label_subset = [col.label for col in self.reflection_file.columns if
                            col.type == MTZColumnTypes.__getattr__(label.name).value]
            matches = list(filter(label.value.match, label_subset))
            if any(matches):
                self.__setattr__(label.name, matches[0].encode('utf-8'))


