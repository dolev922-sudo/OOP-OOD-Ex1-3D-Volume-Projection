"""Slow scalar oracle for the documented row interpolation (tests only)."""
from math import dist

import numpy as np


def scalar_projection(data, vertices):
    """No production geometry, dimension, sampling or projection helpers."""
    if len(vertices) == 3:
        lt, lb, rb = vertices
        rt = lt
    else:
        lt, rt, lb, rb = vertices
    height = max(2, round(max(dist(lt, lb), dist(rt, rb))) + 1)
    width = max(2, round(dist(lb, rb)) + 1)
    output = np.zeros((height, width), dtype=data.dtype)
    for y in range(height):
        t = y / (height - 1)
        left = [lt[k] + t * (lb[k] - lt[k]) for k in range(3)]
        right = [rt[k] + t * (rb[k] - rt[k]) for k in range(3)]
        count = max(1, round(dist(left, right)) + 1)
        start = (width - count) // 2
        for j in range(count):
            x = start + j
            if not 0 <= x < width:
                continue
            u = j / (count - 1) if count > 1 else 0
            p = [left[k] + u * (right[k] - left[k]) for k in range(3)]
            if all(0 <= p[k] <= data.shape[k] - 1 for k in range(3)):
                output[y, x] = data[tuple(round(v) for v in p)]
    return output
