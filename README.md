# Researched-Based-Surf-Tracker

## Overview
This project is a surf tracker which is pretty much a more user specified version of surfline. The data is comprised of buoy and wind/tide data from various sources, focused around Beacons Beach, Encinitas CA, and the rated sample is based off of my subjective rating given the input data. The project tests this data on various ML models to assess the accuracy of their ratings.

## Project Goal
I am attempting to rebuild an old model of mine with a much more technical, ML and research backed approach, touching on efficiency of specific models, how an ML model processes data, what/how models work best with limited information, and more. The overarching goal is to establish thersholds for which modesl thrive on different levels of input data, specifically 10, 25, 50, 75, 100, and 150 inputs. This will be tested on 7 models, Ridge Regression, Random Forest, Neural Network, kNN, Gaussian Processing, xgBoost, and tabpfn, with their errors in relation to my personally rated data as well as the standard deviations used for analysis.

## Data
I am using public data listed in "data_info.md". This includes NOAA bouy NDBC station 46237 for 2025, NOAA tides and current tracker station 9414290 for 2025, and Open Metro historical wind data, as well as surfline to fill in various gaps and check the accuracy of my personal ratings on a small scale.

## Personalization
The long term goal is to have a system where a user can input a specific location, as well as their prefered surf conditions, and the model will be able to use the users previously logged data (which can be done after each session at the beach) or historic data from the public data sources, and it will output a ranking out of 10 for how close the surf will match the users desires. This research project acts as a foundational system as well as determination for which models would be best to use in the case where I expand the project as mentioned.

## Planned Development
- Data visualiztion
- Clean up code
- Make it outside-user friendly and personalizable