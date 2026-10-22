# part3.py

import csv
import os
from datetime import datetime, timedelta
from bisect import bisect_left

from part1 import merge_dir


def detect_bursts(path: str, m: int, t: timedelta, b: int) -> tuple[int, list[dict]]:
    """
    Return the count and event rows for greedy non-overlapping bursts.
    :param path:    Path of log file.
    :param m:       Minimum number of events in a burst.
    :param t:       Maximum timespan of a burst.
    :param b:       Number of elements for base case.
    :return:        (Number of bursts, details of bursts)
    """
    if m <= 0:
        raise ValueError("m must be positive.")
    if t < timedelta(0):
        raise ValueError("t must be non-negative.")
    if b <= 0:
        raise ValueError("b must be positive.")

    def to_datetime(line) -> datetime:
        s = f"{line[2]} {line[3]}"
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S,%f")

    lines = []
    times = []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for line in reader:
            lines.append(line)
            times.append(to_datetime(line))

    def slice_to_info(start, end) -> dict:
        """Convert slice of lines/times arrays into an info dictionary."""
        return {
            'start_time': times[start],
            'end_time': times[end],
            'start_idx': start,
            'end_idx': end,
            'lines': lines[start:end + 1]
        }

    def recurse(start: int, end: int) -> set[int]:
        """Find starts of minimally qualifying (potentially overlapping) bursts between start and end of times."""
        if end - start <= b:
            # Base case: the size of the checked area is less than b.
            # Return set of starting indexes of all minimally qualifying bursts.
            return {i for i in range(start, end - m + 1) if times[i + m - 1] - times[i] < t}

        # Recursively find the number of bursts in each half of the list.
        mid = (start + end) // 2
        candidates = recurse(start, mid) | recurse(mid, end)

        # Search for candidates that span the median.
        first = max(start, mid - m + 1)     # only the m elements closest to median on either side are searched
        last = min(mid - 1, end - m)
        for i in range(first, last + 1):
            if times[i + m - 1] - times[i] < t:
                candidates.add(i)

        return candidates

    # Recursively find all potential candidates.
    candidates = recurse(0, len(times))

    # Merge overlapping bursts into the largest combined burst with a timespan less than t.
    bursts = []
    start = 0
    while start <= len(times) - m:
        if start not in candidates:
            start += 1
            continue

        end = bisect_left(times, times[start] + t, start) - 1   # idx of the latest element <t away from start
        bursts.append(slice_to_info(start, end))
        start = end + 1     # skip past all elements in the new burst

    return len(bursts), bursts


if __name__ == "__main__":
    PATH = "merged_log.csv"
    if not os.path.exists(PATH):
        merge_dir("data", PATH)

    num_bursts, bursts = detect_bursts(PATH, 20, timedelta(seconds=1), 5)
    print(f"{num_bursts} bursts were found in the data.")
    for burst in bursts:
        print(f"Timespan: {burst['end_time'] - burst['start_time']} | Number of logs: {len(burst['lines'])} | idx: {burst['lines'][0][0]}")
