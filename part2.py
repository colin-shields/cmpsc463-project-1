# part2.py

import csv
import numpy as np
import os

from part1 import merge_dir

np.set_printoptions(threshold=np.inf)

COMPONENT_COL = 6   # column of components in csv file


def build_dependency_matrix(path: str):
    """Build a component dependency matrix from a csv file at path."""

    components_map = {}  # {component_name: index_in_matrix}

    idx = 0
    lines = []  # store lines in memory so the file is only opened once

    # Build components map.
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for line in reader:
            lines.append(line)
            if line[COMPONENT_COL] not in components_map:
                components_map[line[COMPONENT_COL]] = idx
                idx += 1

    # Build empty matrix.
    size = len(components_map)
    mat = np.zeros((size, size))

    # Fill matrix with dependent connections.
    prev_idx = None
    for i, line in enumerate(lines):
        cur_idx = components_map.get(line[COMPONENT_COL], None)
        if prev_idx is not None and cur_idx is not None:
            mat[prev_idx, cur_idx] = 1
        prev_idx = cur_idx

    return mat, components_map


def strassen_mult(arr1, arr2):
    """Multiply two matrices using Strassen's recursive algorithm."""

    def matrix_mul_recurse(arr1, arr2):
        """Multiply two matrices whose dimensions are powers of 2."""

        if len(arr1[0]) == 1 and len(arr2[0]) == 1:
            return [[arr1[0][0] * arr2[0][0]]]

        def add_matrix(a1, a2):
            added = []
            for i in range(len(a1)):
                rslt = []
                for j in range(len(a1[0])):
                    rslt.append(a1[i][j] + a2[i][j])
                added.append(rslt)
            return added

        def sub_matrix(a1, a2):
            subtract = []
            for i in range(len(a1)):
                rslt = []
                for j in range(len(a1[0])):
                    rslt.append(a1[i][j] - a2[i][j])
                subtract.append(rslt)
            return subtract

        # Split matrix into 8 subarrays.
        a = [arr1[i][:len(arr1[0]) // 2] for i in range(len(arr1) // 2)]
        b = [arr1[i][len(arr1[0]) // 2:] for i in range(len(arr1) // 2)]
        c = [arr1[i][:len(arr1[0]) // 2] for i in range(len(arr1) // 2, len(arr1))]
        d = [arr1[i][len(arr1[0]) // 2:] for i in range(len(arr1) // 2, len(arr1))]
        e = [arr2[i][:len(arr2[0]) // 2] for i in range(len(arr2) // 2)]
        f = [arr2[i][len(arr2[0]) // 2:] for i in range(len(arr2) // 2)]
        g = [arr2[i][:len(arr2[0]) // 2] for i in range(len(arr2) // 2, len(arr2))]
        h = [arr2[i][len(arr2[0]) // 2:] for i in range(len(arr2) // 2, len(arr2))]

        # Recursively compute the 7 products.
        p1 = matrix_mul_recurse(a, sub_matrix(f, h))
        p2 = matrix_mul_recurse(add_matrix(a, b), h)
        p3 = matrix_mul_recurse(add_matrix(c, d), e)
        p4 = matrix_mul_recurse(d, sub_matrix(g, e))
        p5 = matrix_mul_recurse(add_matrix(a, d), add_matrix(e, h))
        p6 = matrix_mul_recurse(sub_matrix(b, d), add_matrix(g, h))
        p7 = matrix_mul_recurse(sub_matrix(a, c), add_matrix(e, f))

        # Recombine the arrays into the full multiplied matrix.

        term1 = sub_matrix(add_matrix(add_matrix(p5, p4), p6), p2)
        term2 = add_matrix(p1, p2)
        term3 = add_matrix(p3, p4)
        term4 = sub_matrix(add_matrix(p1, p5), add_matrix(p3, p7))

        result = []

        for ele1, ele2 in zip(term1, term2):
            result.append(ele1 + ele2)

        for ele1, ele2 in zip(term3, term4):
            result.append(ele1 + ele2)

        return result

    arr_size = len(arr1)
    if arr_size != len(arr2):
        raise ValueError("Cannot use Strassen multiplication on two matrices of different lengths.")

    # Pad matrices so their dimensions are powers of 2.

    num = 1
    while num < arr_size:
        num *= 2

    pad_size = num - arr_size
    padded1 = np.pad(arr1, (0, pad_size)) if pad_size != 0 else arr1
    padded2 = np.pad(arr2, (0, pad_size)) if pad_size != 0 else arr2

    # Multiply and remove padding.
    mult = np.array(matrix_mul_recurse(padded1, padded2))
    if pad_size != 0:
        return mult[:-pad_size, :-pad_size]
    return mult


if __name__ == '__main__':
    PATH = "merged_log.csv"
    if not os.path.exists(PATH):
        merge_dir("data", PATH)

    A, comp_map = build_dependency_matrix(PATH)
    print(A)
    print()
    A2 = strassen_mult(A, A)
    print(A2)
    print()
    A3 = strassen_mult(A2, A)
    print(A3)

    npA2 = A @ A
    npA3 = A2 @ A

    if np.allclose(A3, npA3):
        print("Strassen multiplication returned same result as numpy.")
    else:
        print("Strassen multiplication failed.")
