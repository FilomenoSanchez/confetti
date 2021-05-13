import random
from confetti.io.parser import Parser
from dials.util.slice import slice_experiments
from dials.util.phil import FilenameDataWrapper
from dxtbx.model.experiment_list import ExperimentListFactory


class Experiments(Parser):

    def _parse(self):
        self.data = self.read_experiments(self.fname)
        self._register_data()

    @staticmethod
    def read_experiments(fname):
        wrapper = FilenameDataWrapper(
            filename=fname,
            data=ExperimentListFactory.from_json_file(fname, check_format=True)
        )
        return wrapper.data

    def _register_data(self):
        self.templates = []
        for imageset in self.data.imagesets():
            self.templates.append(imageset.get_template())

        self.imagesets = []
        self.imagesets_angles = []
        for imageset in self.data.imagesets():
            self.imagesets.append(imageset.paths())
            scan = imageset.get_scan()
            angles = []
            for image_idx in range(1, len(imageset.paths()) + 1):
                angles.append(scan.get_angle_from_image_index(image_idx))
            self.imagesets_angles.append(angles)

        self.identifiers = []
        for experiment in self.data:
            self.identifiers.append(experiment.identifier)

    def slice_experiments(self, angle_threshold, discard_sweeps_outside=False, random_start=False):
        identifiers_to_remove = []
        new_image_ranges = []
        for experiment in self.data:
            angle_range = [experiment.scan.get_angle_from_image_index(i) for i in
                           range(1, experiment.imageset.size() + 1)]
            initial_angle = angle_range[0]
            final_angle = angle_range[-1]
            total_angle_gain = abs(initial_angle - final_angle)

            if discard_sweeps_outside and total_angle_gain < angle_threshold:
                identifiers_to_remove.append(experiment.identifier)
                continue
            elif not random_start:
                for idx, angle in enumerate(angle_range, 1):
                    if abs(angle - initial_angle) >= angle_threshold and len(range(0, idx)) != 0:
                        new_image_ranges.append((1, idx))
                        break
            else:
                last_valid_start_idx = None
                for idx, value in enumerate(angle_range[::-1]):
                    if idx == len(angle_range) - 1:
                        break
                    real_idx = len(angle_range) - idx - 1
                    angle_gain = abs(final_angle - angle_range[real_idx])
                    if angle_gain >= angle_threshold:
                        last_valid_start_idx = real_idx
                        break
                if last_valid_start_idx is not None:
                    start = random.randint(0, last_valid_start_idx)
                    initial_angle = angle_range[start]
                    for idx, angle in enumerate(angle_range[start:], start + 1):
                        if abs(angle - initial_angle) >= angle_threshold and len(range(start, idx)) != 0:
                            new_image_ranges.append((start + 1, idx))
                            break
                else:
                    identifiers_to_remove.append(experiment.identifier)

        if any(identifiers_to_remove):
            self.data.remove_on_experiment_identifiers(identifiers_to_remove)
        self.data = slice_experiments(self.data, new_image_ranges)
        self._register_data()
