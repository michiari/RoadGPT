# RoadGPT
 
RoadGPT is a program that was written as part of my Bachelor Thesis. It aims to facilitate the automated generation of 3D-roads by leveraging the power of ChatGPT. The user provides a textual description of a road and RoadGPT translates that description into coordinates which are then used to simulate a car driving on a road matching that description in BeamNG.tech.

## Prerequisites

Python 3.9 \
BeamNG.tech v0.26 \
OpenAI API Key stored in a .env file as OPENAI_API_KEY

## How to use RoadGPT

The program can be executed by running the run_roadgpt.py file and providing the following Parameters:

- beamng-home: BeamNG.tech folder
- beamng-user: folder created by User to store leveldata, etc.

The program will then ask for a description of a road and the number of times it should attempt to generate roads with the given prompt.

After RoadGPT has exhausted the number of trys it will ask for a new prompt. You can either provide a new prompt or quit the program by typing "exit". If you exit the program, it will process the results and generate two Excel files containing the data.

## Example prompts:

"Create a mountain road with serpentines" \
"Create a road with 3 uphill turns and 2 downhill turns."

## Publications

ICSE 2025 New Ideas and Emerging Results (NIER): https://conf.researchr.org/details/icse-2025/icse-2025-nier/12/Automatically-Generating-Content-for-Testing-Autonomous-Vehicles-from-User-Descriptio
