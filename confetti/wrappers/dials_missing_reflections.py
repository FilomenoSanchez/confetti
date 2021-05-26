import io
import os
from cctbx import uctbx
from confetti.wrappers.wrapper import Wrapper
from confetti.io import Experiments, Reflections
from dials.report.analysis import scaled_data_as_miller_array
from dials.util import missing_reflections, tabulate
from dials.util.filter_reflections import filtered_arrays_from_experiments_reflections
from dials.util.options import OptionParser, flatten_experiments, flatten_reflections
from dials.util.multi_dataset_handling import assign_unique_identifiers, parse_multiple_datasets


class DialsMissingReflections(Wrapper):

    def __init__(self, workdir, min_component_size=0):
        self.experiments_fname = os.path.join(workdir, 'scaled.expt')
        self.reflections_fname = os.path.join(workdir, 'scaled.refl')
        self.experiments = None
        self.reflections = None
        self.min_component_size = min_component_size
        self.connected_reflections_percentage = 0
        super(DialsMissingReflections, self).__init__(workdir=workdir)

    @property
    def keywords(self):
        return None

    @property
    def logfile(self):
        return None

    @property
    def expected_output(self):
        return None

    @property
    def cmd(self):
        return None

    def _run(self):
        try:
            self.__run()
        except Exception as e:
            self.logger.error('Dials missing reflections execution found an exception: {}'.format(e))

    def _parse_logfile(self):
        pass

    def __run(self):
        if not os.path.isfile(self.experiments_fname) or not os.path.isfile(self.reflections_fname):
            self.error = True
            self.logger.error('Input files not found for dials.missing_reflections')
            return
        self.experiments = Experiments(self.experiments_fname)
        self.reflections = Reflections(self.reflections_fname)
        experiments = flatten_experiments([self.experiments])
        reflections = flatten_reflections([self.reflections])

        if len(reflections) != 1 and len(experiments) != len(reflections):
            self.logger.error("Number of experiments must equal the number of reflection tables")
            return

        reflections = parse_multiple_datasets(reflections)
        experiments, reflections = assign_unique_identifiers(experiments, reflections)

        if all("inverse_scale_factor" in refl for refl in reflections):
            # Assume all arrays have been scaled
            miller_array = scaled_data_as_miller_array(reflections, experiments, anomalous_flag=False)
        else:
            # Else get the integrated intensities
            miller_arrays = filtered_arrays_from_experiments_reflections(experiments, reflections)
            miller_array = miller_arrays[0]
            for ma in miller_arrays[1:]:
                miller_array = miller_array.concatenate(ma)

        # Print overall summary of input miller array
        s = io.StringIO()
        ma_unique = miller_array.unique_under_symmetry()
        ma_unique.show_comprehensive_summary(f=s)

        # Get the regions of missing reflections
        complete_set, unique_ms = missing_reflections.connected_components(miller_array)
        unique_ms = [ms for ms in unique_ms if ms.size() >= self.min_component_size]

        # Print some output for user
        if len(unique_ms):
            n_expected = complete_set.size()
            for ms in unique_ms:
                self.connected_reflections_percentage += 100 * ms.size() / n_expected
        else:
            self.connected_reflections_percentage = 0
            self.logger.warning("No connected regions of missing reflections identified")
