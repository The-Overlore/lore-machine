import json
import math
from typing import Any


def calculate_cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot_prod = 0.0
    v1_sqr_sum = 0.0
    v2_sqr_sum = 0.0

    for i in range(len(v1)):
        dot_prod += v1[i] * v2[i]
        v1_sqr_sum += v1[i] ** 2
        v2_sqr_sum += v2[i] ** 2

    return dot_prod / (math.sqrt(v1_sqr_sum) * math.sqrt(v2_sqr_sum))


def save_to_file(discussion: str, rowid: int, embedding: str) -> None:
    with open("Output.json", "a") as file:
        data_to_save = {"rowid": rowid, "discussion": discussion, "embedding": embedding}
        json.dump(data_to_save, file)
        file.write("\n")


# def serialize(vector: list[float]) -> bytes:
#         """serializes a list of floats into a compact "raw bytes" format"""
#         return struct.pack("%sf" % len(vector), *vector)


def find_lowest_second_param(data: Any) -> Any:
    lowest_dict = min(data, key=lambda x: list(x.values())[0])
    return list(lowest_dict.keys())[0]


def find_closest_to_one(data: Any) -> Any:
    closest_key = None
    closest_value = float("-inf")

    for d in data:
        key, value = list(d.items())[0]

        if closest_value < value <= 1:
            closest_value = value
            closest_key = key

    return closest_key
