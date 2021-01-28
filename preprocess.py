"""Module to read json files and concatenate into one csv file per 'person'
"""
import os
import simplejson as json
import pandas as pd


def read_files(file_list):
    """Read in all the json files, and export a single dataframe"""
    data = []  # an empty list to store the json files

    for file in file_list:
        with open(file) as f:
            data.extend(json.load(f))  # Read data frame from json file

    return pd.DataFrame.from_records(data)


def get_file_list():
    files = os.listdir("./input")


if __name__ == "__main__":
