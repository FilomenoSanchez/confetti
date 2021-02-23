import os
import pyjob
import logging


class Cluster(object):

    def __init__(self, id, workdir):
        self.id = id
        self.workdir = os.path.join(workdir, 'cluster_{}'.format(id))
        self.error = False
        self.dials_exe = 'dials'
        self.logger = logging.getLogger(__name__)
