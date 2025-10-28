from math import sqrt
from enum import Enum
import logging as log

from self_driving.bbox import RoadBoundingBox
import numpy as np

# from code_pipeline.tests_generation import RoadTest
from code_pipeline.tests_generation import RoadTestFactory


MIN_ELEVATION = -28

class ValidationResult(Enum):
    VALID = "valid"
    WRONG_TYPE = "wrong_type"
    NOT_ENOUGH_POINTS = "not_enough_points"
    TOO_MANY_POINTS = "too_many_points"
    NOT_INSIDE_MAP = "not_inside_map"
    INTERSECTS_BOUNDARY = "intersects_boundary"
    INVALID_POLYGON = "invalid_polygon"
    NOT_MINIMUM_LENGTH = "not_minimum_length"
    TOO_SHARP = "too_sharp"
    TOO_STEEP = "too_steep"


def get_validation_message(result: ValidationResult) -> str:
    """
    Returns a human-readable validation message for the given validation result.
    
    Args:
        result: A ValidationResult enum value
        
    Returns:
        A string describing the validation result
    """
    messages = {
        ValidationResult.VALID: "Test is valid",
        ValidationResult.WRONG_TYPE: "Wrong type",
        ValidationResult.NOT_ENOUGH_POINTS: "Not enough road points.",
        ValidationResult.TOO_MANY_POINTS: "The road definition contains too many points",
        ValidationResult.NOT_INSIDE_MAP: "Not entirely inside the map boundaries",
        ValidationResult.INTERSECTS_BOUNDARY: "Not entirely inside the map boundaries",
        ValidationResult.INVALID_POLYGON: "The road is self-intersecting",
        ValidationResult.NOT_MINIMUM_LENGTH: "The road is not long enough.",
        ValidationResult.TOO_SHARP: "The road is too sharp",
        ValidationResult.TOO_STEEP: "The road is too steep",
        ValidationResult.UNDERGROUND: "The road goes underground",
    }
    return messages.get(result, "Unknown validation result")


def find_circle(p1, p2, p3):
    """
    Returns the center and radius of the circle passing the given 3 points.
    In case the 3 points form a line, returns (None, infinity).
    """
    temp = p2[0] * p2[0] + p2[1] * p2[1]
    bc = (p1[0] * p1[0] + p1[1] * p1[1] - temp) / 2
    cd = (temp - p3[0] * p3[0] - p3[1] * p3[1]) / 2
    det = (p1[0] - p2[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p2[1])

    if abs(det) < 1.0e-6:
        return np.inf

    # Center of circle
    cx = (bc*(p2[1] - p3[1]) - cd*(p1[1] - p2[1])) / det
    cy = ((p1[0] - p2[0]) * cd - (p2[0] - p3[0]) * bc) / det

    radius = np.sqrt((cx - p1[0])**2 + (cy - p1[1])**2)
    return radius


def min_radius(x, w=5):
    mr = np.inf
    nodes = x
    for i in range(len(nodes) - w):
        p1 = nodes[i]
        p2 = nodes[i + int((w-1)/2)]
        p3 = nodes[i + (w-1)]
        radius = find_circle(p1, p2, p3)
        if radius < mr:
            mr = radius
    if mr == np.inf:
        mr = 0

    return mr * 3.280839895#, mincurv

class TestValidator:

    def __init__(self, map_size, min_road_length=20):
        self.map_size = map_size
        self.box = (0, 0, map_size, map_size)
        self.road_bbox = RoadBoundingBox(self.box)
        self.min_road_length = min_road_length
        # Not sure how to set this value... This might require to compute some sort of density: not points that are too
        # close to each others
        self.max_points = 500

    def is_enough_road_points(self, the_test):
        return len(the_test.road_points) > 1

    def is_too_many_points(self, the_test):
        return len(the_test.road_points) > self.max_points

    def is_not_self_intersecting(self, the_test):
        road_polygon = the_test.get_road_polygon()
        return road_polygon.is_valid()

    def is_too_sharp(self, the_test, TSHD_RADIUS=47):
        if TSHD_RADIUS > min_radius(the_test.road_points) > 0.0:
            check = True
        else:
            check = False
        return check

    def is_inside_map(self, the_test):
        """
            Take the extreme points and ensure that their distance is smaller than the map side
        """
        xs = [t[0] for t in the_test.road_points]
        ys = [t[1] for t in the_test.road_points]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        log.info(f"X road extremes: {min_x} to {max_x}")
        log.info(f"Y road extremes: {min_y} to {max_y}")

        return 0 < min_x or min_x > self.map_size and \
               0 < max_x or max_x > self.map_size and \
               0 < min_y or min_y > self.map_size and \
               0 < max_y or max_y > self.map_size

    def is_right_type(self, the_test):
        """
            The type of the_test must be RoadTest
        """
        check = type(the_test) is RoadTestFactory.RoadTest
        return check

    def is_valid_polygon(self, the_test):
        road_polygon = the_test.get_road_polygon()
        check = road_polygon.is_valid()
        return check

    def intersects_boundary(self, the_test):
        road_polygon = the_test.get_road_polygon()
        check = self.road_bbox.intersects_boundary(road_polygon.polygon)
        return check

    def is_minimum_length(self, the_test):
        return the_test.get_road_length(interpolate_road_points=True) > self.min_road_length
    
    def get_distance_altitude(self, road_points):
        d = [0]
        z = [road_points[0][2]]
        for i in range(1, len(road_points)):
            d.append(d[-1] + sqrt((road_points[i][0] - road_points[i-1][0])**2 + (road_points[i][1] - road_points[i-1][1])**2))
            z.append(road_points[i][2])
        return list(zip(d, z))
    
    def is_too_steep(self, the_test):
        if not isinstance(the_test, list):
            nodes = self.get_distance_altitude(the_test.interpolated_points)
            # log.info("DISTANCE NODES:", nodes)
        else:
            nodes = the_test
        grouped_nodes = [nodes[pos:pos + 10] for pos in range(0, len(nodes), 10)]
        mean_alt_diff = []
        for group in grouped_nodes:
            alt_diffs = []
            for i in range(1, len(group)):
                alt_diff = (group[i][1] - group[i-1][1]) / (group[i][0] - group[i-1][0])
                alt_diffs.append(alt_diff)
            mean_alt_diff.append((np.mean(alt_diffs)))
        for i in range(0, len(mean_alt_diff)):
            if mean_alt_diff[i] > 0.15:
                print(mean_alt_diff[i])
                return True

        return False

    def goes_underground(self, the_test):
        for point in the_test.road_points:
            if point[2] < MIN_ELEVATION:
                return True
        return False

    def validate_test(self, the_test) -> tuple[bool, ValidationResult]:
        """
        Validates a road test and returns validation status and result.
        
        Args:
            the_test: The road test to validate
            
        Returns:
            A tuple of (is_valid, validation_result) where is_valid is a boolean
            and validation_result is a ValidationResult enum value
        """

        if not self.is_right_type(the_test):
            log.error("right type", type(the_test))
            return False, ValidationResult.WRONG_TYPE

        if not self.is_enough_road_points(the_test):
            log.error("enough road points")
            return False, ValidationResult.NOT_ENOUGH_POINTS

        if self.is_too_many_points(the_test):
            log.error("too many points")
            return False, ValidationResult.TOO_MANY_POINTS

        if not self.is_inside_map(the_test):
            log.error("inside map")
            return False, ValidationResult.NOT_INSIDE_MAP

        if self.intersects_boundary(the_test):
            log.error("intersects boundary")
            return False, ValidationResult.INTERSECTS_BOUNDARY

        if not self.is_valid_polygon(the_test):
            log.error("is valid polygon")
            return False, ValidationResult.INVALID_POLYGON

        if not self.is_minimum_length(the_test):
            log.error("is minimum length")
            return False, ValidationResult.NOT_MINIMUM_LENGTH

        if self.is_too_sharp(the_test):
            log.error("is too sharp")
            return False, ValidationResult.TOO_SHARP
        
        if self.is_too_steep(the_test):
            log.error("is too steep")
            return False, ValidationResult.TOO_STEEP

        if self.goes_underground(the_test):
            log.error("goes underground")
            return False, ValidationResult.UNDERGROUND

        return True, ValidationResult.VALID
