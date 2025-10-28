from self_driving.road_polygon import RoadPolygon
from shapely.geometry import LineString
from scipy.interpolate import splev, splprep, RectBivariateSpline, interp2d
from numpy.ma import arange
from shapely.geometry import LineString
import json
import numpy as np
# Constants
rounding_precision = 3
interpolation_distance = 1
smoothness = 0
min_num_nodes = 20
MAX_GRADIENT = 15
mutation_probability = 0.2


def _interpolate(the_test):
    """
        Interpolate the road points using cubic splines and ensure we handle 4F tuples for compatibility
    """
    old_x_vals = [t[0] for t in the_test]
    old_y_vals = [t[1] for t in the_test]
    old_z_vals = [t[2] for t in the_test]

    # This is an approximation based on whatever input is given
    test_road_length = LineString([(t[0], t[1]) for t in the_test]).length
    num_nodes = int(test_road_length / interpolation_distance)
    if num_nodes < min_num_nodes:
        num_nodes = min_num_nodes

    assert len(old_x_vals) >= 2, "You need at least two road points to define a road"
    assert len(old_y_vals) >= 2, "You need at least two road points to define a road"
    assert len(old_z_vals) >= 2, "You need at least two road points to define a road"

    if len(old_x_vals) == 2:
        # With two points the only option is a straight segment
        k = 1
    elif len(old_x_vals) == 3:
        # With three points we use an arc, using linear interpolation will result in invalid road tests
        k = 2
    else:
        # Otheriwse, use cubic splines
        k = 3

    pos_tck, pos_u = splprep([old_x_vals, old_y_vals, old_z_vals], s=smoothness, k=k)

    step_size = 1 / num_nodes
    unew = arange(0, 1 + step_size, step_size)

    new_x_vals, new_y_vals, new_z_vals = splev(unew, pos_tck)

    # Return the 4-tuple with default z and defatul road width
    return list(zip([round(v, rounding_precision) for v in new_x_vals],
                    [round(v, rounding_precision) for v in new_y_vals],
                    [v for v in new_z_vals],
                    [8.0 for v in new_x_vals]))


def _incremental_id_generator():
    test_id = 1
    while True:
        yield test_id
        test_id += 1


class RoadTestFactory:
    # Static variable
    test_id_generator = _incremental_id_generator()

    class RoadTest:
        """
            This class represent a test, i.e., the road that the driving agent should follow.
            Note that this class is nested in the RoadTestFactory to avoid direct creation
        """

        def __init__(self, road_points):
            assert type(road_points) is list, "You must provide a list of road points to create a RoadTest"
            # assert all(len(i) == 2 for i in road_points), "Malformed list of road points"
            # The original input
            self.road_points = road_points[:]
            # The interpolated input
            # self.beamng_road_type = beamng_road_type
            # self.altitude = altitude

            self.interpolated_points = _interpolate(self.road_points)
            # else:
            #     self.interpolated_points = _interpolate(self.road_points, self.beamng_road_type)
            # The rendered road
            self.road_polygon = RoadPolygon.from_nodes(self.interpolated_points)

            # At the beginning we do not know whether the test is valid or not
            self.is_valid = None
            self.validation_message = None

        def get_road_polygon(self):
            return self.road_polygon

        def get_road_length(self, interpolate_road_points: bool = False):
            if interpolate_road_points:
                return LineString([(t[0], t[1], t[2]) for t in _interpolate(self.interpolated_points)]).length
            return LineString([(t[0], t[1], t[2]) for t in self.interpolated_points]).length

        def set_validity(self, is_valid, validation_message):
            self.is_valid = is_valid
            self.validation_message = validation_message

        def to_json(self):
            theobj = {}
            # Statically generated attributes
            theobj['is_valid'] = self.is_valid
            theobj['validation_message'] = str(self.validation_message)
            theobj['road_points'] = self.road_points
            theobj['interpolated_points'] = [(p[0], p[1], p[2]) for p in self.interpolated_points]
            # Dynamically generated attributes.
            # https://stackoverflow.com/questions/610883/how-to-know-if-an-object-has-an-attribute-in-python
            # "easier to ask for forgiveness than permission" (EAFP)
            try:
                theobj['id'] = self.id
            except AttributeError:
                pass

            try:
                theobj['execution_data'] = self.execution_data
            except AttributeError:
                pass

            try:
                theobj['test_outcome'] = self.test_outcome
            except AttributeError:
                pass

            try:
                theobj['description'] = self.description
            except AttributeError:
                pass

            try:
                theobj['features'] = self.features
            except AttributeError:
                pass

            return json.dumps(theobj)

    @staticmethod
    def create_road_test(road_points):
        road_test = RoadTestFactory.RoadTest(road_points)
        # TODO Why not simply declare the id as field of RoadTest?
        # Generate the new id. Call next otherwise we return the generator
        setattr(road_test, 'id', next(RoadTestFactory.test_id_generator))
        return road_test

    # class RoadTest3D(RoadTest):
    #     def __init__(self, road_points, beamng_road_type, altitude=None):
    #         # road_points_3d = self._calculate_z_vals(road_points, altitude)
    #         # super().__init__(road_points_3d, beamng_road_type, altitude)

    #     def _calculate_distance(self, node1, node2):
    #         distance = np.sqrt((node2[0] - node1[0]) ** 2 + (node2[1] - node1[1]) ** 2)
    #         return distance

    #     def _calculate_diff(self, node1, node2, dist):
    #         distance = self._calculate_distance(node1, node2)
    #         diff = distance/dist
    #         return diff

    #     def _calculate_max_height(self, distance):
    #         max_height_diff = distance * (MAX_GRADIENT / 100)
    #         max_height_diff = round(max_height_diff, 3)
    #         return max_height_diff

    #     def _interpolate_height_points(self, vals):
    #         """
    #             Interpolate the road points using cubic splines and ensure we handle 4F tuples for compatibility
    #         """

    #         d_vals = [v[0] for v in vals]
    #         z_vals = [v[1] for v in vals]

    #         # This is an approximation based on whatever input is given
    #         test_road_lenght = d_vals[-1]
    #         num_nodes = int(test_road_lenght / interpolation_distance)
    #         if num_nodes < min_num_nodes:
    #             num_nodes = min_num_nodes

    #         assert len(d_vals) >= 2, "You need at least two road points to define a road"
    #         assert len(z_vals) >= 2, "You need at least two road points to define a road"

    #         if len(d_vals) == 2:
    #             # With two points the only option is a straight segment
    #             k = 1
    #         elif len(d_vals) == 3:
    #             # With three points we use an arc, using linear interpolation will result in invalid road tests
    #             k = 2
    #         else:
    #             # Otheriwse, use cubic splines
    #             k = 3

    #         pos_tck, pos_u = splprep([d_vals, z_vals], s=smoothness, k=k)

    #         step_size = 1 / num_nodes
    #         unew = arange(0, 1 + step_size, step_size)

    #         new_d_vals, new_z_vals = splev(unew, pos_tck)

    #         return list(zip([round(v, rounding_precision) for v in new_d_vals],
    #                         [round(v, rounding_precision) for v in new_z_vals]))

    #     def _calculate_z_vals(self, road_points, altitude):
    #         if altitude is None:
    #             altitude = -28

    #         road_point_indexes = [] # store the indexes for altitude mutation
    #         start = None
    #         distances = [0]
    #         for i in range(1, len(road_points)):
    #             """
    #             calculate the distance from the start to every roadpoint
    #             """
    #             distances.append(distances[-1] + self._calculate_distance(road_points[i-1], road_points[i]))

    #             if round(self._calculate_distance(road_points[0], road_points[i]), 0) >= 5:
    #                 start = i+1
    #                 break

    #         for i in range(start, len(road_points)-1):

    #             distances.append(distances[-1] + self._calculate_distance(road_points[i - 1], road_points[i]))

    #             if np.random.uniform(0, 1) < mutation_probability:
    #                 road_point_indexes.append(i)

    #         road_point_indexes.append(len(road_points)-1)
    #         distances.append(distances[-1] + self._calculate_distance(road_points[-2], road_points[-1]))

    #         interpolation_points = [[0, altitude], [distances[start-1], altitude]]

    #         for i in range(len(road_point_indexes)):
    #             ind = road_point_indexes[i]
    #             max_diff = self._calculate_max_height(distances[ind] - interpolation_points[-1][0])
    #             height_diff = np.random.uniform(-max_diff, max_diff)

    #             if height_diff < 0 and interpolation_points[-1][1] + height_diff < -28:
    #                 height_diff = abs(height_diff)

    #             height = interpolation_points[-1][1] + height_diff

    #             interpolation_points.append([distances[ind], height])

    #         new_points = self._interpolate_height_points(interpolation_points)

    #         assert len(road_points) == len(distances)

    #         new_road_points = []

    #         for i in range(len(road_points)):
    #             for j in range(i, len(new_points)):
    #                 if round(new_points[j][0], 0) == round(distances[i], 0):
    #                     new_road_points.append([road_points[i][0], road_points[i][1], new_points[j][1]])

    #         return new_road_points


class TestGenerationStatistic:
    """
        Store statistics about test generation
        TODO: Refactor using a RoadTest and RoadTestExecution
        TODO Move to road_statistics package
    """

    def __init__(self):
        self.test_generated = 0
        self.test_valid = 0
        self.test_invalid = 0
        self.test_passed = 0
        self.test_failed = 0
        self.test_in_error = 0
        self.obes = 0

        self.test_generation_real_times = []

        self.test_execution_real_times = []
        self.test_execution_simulation_times = []

        # TODO Capturing this is not that easy. We might approximate it as the time between consecutive
        #  calls to execute_test, but then we need to factor out how long it took to execute them... also
        #  it does not account for invalid tests...
        # self.last_generation_time = time.monotonic()
        # self.test_generation_times = []

    def __str__(self):
        msg = ""
        msg += "test generated: " + str(self.test_generated) + "\n"
        msg += "test valid: " + str(self.test_valid) + "\n"
        msg += "test invalid: " + str(self.test_invalid) + "\n"
        msg += "test passed: " + str(self.test_passed) + "\n"
        msg += "test failed: " + str(self.test_failed) + "\n"
        msg += "test in_error: " + str(self.test_in_error) + "\n"

        msg += "(real) time spent in generation :" + str(sum(self.test_generation_real_times)) + "\n"
        msg += "(real) time spent in execution :" + str(sum(self.test_execution_real_times)) + "\n"
        msg += "(simulated) time spent in execution :" + str(sum(self.test_execution_simulation_times)) + "\n"
        return msg

    def as_csv(self):
        # TODO There's definitively a more python way to do this
        header = ",".join(["test_generated", "test_valid", "test_invalid", "test_passed", "test_failed",
                           "test_in_error", "real_time_generation", "real_time_execution", "simulated_time_execution"])
        values = ",".join([str(self.test_generated), str(self.test_valid), str(self.test_invalid),
                           str(self.test_passed), str(self.test_failed), str(self.test_in_error),
                           str(sum(self.test_generation_real_times)), str(sum(self.test_execution_real_times)),
                           str(sum(self.test_execution_simulation_times))])
        return '\n'.join([header, values])