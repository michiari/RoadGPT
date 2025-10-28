import math
import numpy as np
import json

from shapely.geometry import LineString
from scipy.interpolate import splev, splprep
from code_pipeline.tests_generation import RoadTestFactory

class RoadGenerator:
    def __init__(self, starting_point, theta, segments):
        self.starting_point = self.set_starting_point(starting_point)
        self.segments = segments
        self.nodes = [self.starting_point]
        self.theta = theta
        self.interpolated_nodes = None

    def set_starting_point(self, starting_point):
        return (starting_point[0] + 5, starting_point[1] + 5, starting_point[2])

    def translate_to_nodes(self):
        self.calculate_next_node(5, 0)
        for segment in self.segments:
            if segment["direction"] == "straight":
                self.calculate_next_node(segment["distance"], segment["incline"])
                continue
            elif segment["direction"] == "left" and segment["turn_degrees"] < 0 or segment["direction"] == "right" and segment["turn_degrees"] > 0:
                self.theta -= segment["turn_degrees"]
            else:
                self.theta += segment["turn_degrees"]

            self.calculate_next_node(segment["distance"], segment["incline"])

    
    def deg_to_rad(self, degrees):
        return degrees * math.pi / 180
    

    def calculate_incline(self, distance, incline):
        return round(distance * (incline / 100), 1)
    
    
    def calculate_next_node(self, distance, incline):
        angle_rad = self.deg_to_rad(self.theta)

        x_start, y_start, z_start = self.nodes[-1]

        x_end = x_start + distance * math.cos(angle_rad)
        y_end = y_start + distance * math.sin(angle_rad)
        z_end = z_start + self.calculate_incline(distance, incline)

        new_node = (x_end, y_end, z_end)

        self.nodes.append(new_node)

        return new_node

    def create_road_test(self):
        return RoadTestFactory.create_road_test(self.nodes)

    def start(self, executor):
        print("Road generation node list:")
        print(self.nodes)
        
        self.executor = executor
        the_test = self.create_road_test()
        print(the_test)
        # Send the test for execution
        test_outcome, description, execution_data = self.executor.execute_test(the_test)
        # Plot the OOB_Percentage: How much the car is outside the road?
        oob_percentage = [state.oob_percentage for state in execution_data]
        # log.info("Collected %d states information. Max is %.3f", len(oob_percentage), max(oob_percentage))

        # # Print test outcome
        # log.info("test_outcome %s", test_outcome)
        # log.info("description %s", description)

        import time
        time.sleep(10)
    

    def __repr__(self) -> str:
        return self.nodes
    
    def __str__(self):
        return str(self.nodes)
    
class RoadRegenerator():
    
    def from_json(self, path, filename):
        import os
        with open(os.path.join(path, filename)) as f:
            json_obj = json.load(f)
            print(json_obj)
            self.nodes = json_obj["road_points"]

    def start(self, executor):
        self.executor = executor
        print(self.nodes)
        the_test = RoadTestFactory.create_road_test(self.nodes)
        print(the_test)
        # Send the test for execution
        test_outcome, description, execution_data = self.executor.execute_test(the_test)
        # Plot the OOB_Percentage: How much the car is outside the road?
        oob_percentage = [state.oob_percentage for state in execution_data]
        # log.info("Collected %d states information. Max is %.3f", len(oob_percentage), max(oob_percentage))

        # # Print test outcome
        # log.info("test_outcome %s", test_outcome)
        # log.info("description %s", description)

        import time
        time.sleep(10)
