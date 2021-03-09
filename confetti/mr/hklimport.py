import os
import shutil
import logging
from confetti.wrappers import Ctruncate, Cad, FreeRFlag


class HklImport(object):
    def __init__(self, workdir, hklin, hklout):
        self.hklin = hklin
        self.workdir = os.path.join(workdir, 'hklimport')
        self.hklout = os.path.join(self.workdir, hklout)
        self.logger = logging.getLogger(__name__)
        self.error = False

    @property
    def cad_stdin(self):
        return "\nLABIN FILE 1 ALLIN\nEND\n"

    @property
    def freerflag_stdin(self):
        return "\nCOMPLETE FREE=FreeR_flag\nEND\n"

    @property
    def ctruncate_keywords(self):
        return "-colin '/*/*/[IMEAN,SIGIMEAN]' -colano '/*/*/[I(+),SIGI(+),I(-),SIGI(-)]' -freein '/*/*/[FreeR_flag]'"

    def make_workdir(self):
        if not os.path.isdir(self.workdir):
            os.mkdir(self.workdir)
        if not os.path.isdir(os.path.join(self.workdir, 'freerflag')):
            os.mkdir(os.path.join(self.workdir, 'freerflag'))

    def run(self):
        self.make_workdir()
        shutil.copyfile(self.hklin, os.path.join(self.workdir, 'freerflag', os.path.basename(self.hklin)))

        freerflag = FreeRFlag(os.path.join(self.workdir, 'freerflag'), self.hklin, 'freerflag_tmp.mtz')
        freerflag.run()
        if freerflag.error:
            self.logger.error('Freerflag had an error')
            self.error = True
            return

        cad = Cad(self.workdir, self.hklin, 'cad_tmp.mtz', self.cad_stdin)
        cad.run()
        if cad.error:
            self.logger.error('Cad had an error')
            self.error = True
            return

        ctruncate = Ctruncate(self.workdir, cad.hklout, self.hklout, self.ctruncate_keywords)
        ctruncate.run()
        if ctruncate.error:
            self.logger.error('Ctruncate had an error')
            self.error = True
