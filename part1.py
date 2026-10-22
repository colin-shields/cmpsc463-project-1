# part1.py

import glob
from datetime import datetime
import csv
import os

DATE_COL = 2
TIME_COL = 3


def is_earlier(row1, row2) -> bool:
    """Given two csv rows, return True if row1 has an earlier (or equal) timestamp than row2."""
    s1 = f"{row1[DATE_COL]} {row1[TIME_COL]}"
    dt1 = datetime.strptime(s1, "%Y-%m-%d %H:%M:%S,%f")
    s2 = f"{row2[DATE_COL]} {row2[TIME_COL]}"
    dt2 = datetime.strptime(s2, "%Y-%m-%d %H:%M:%S,%f")

    if dt1 <= dt2:
        return True
    return False


def merge(path1: str, path2: str, out_path: str = "temp.csv") -> str:
    """
    Given two csv files sorted by their timestamps, merge them into a single sorted csv file.
    :return: Output path
    """

    with open(out_path, 'w', newline='') as f0:
        with open(path1, 'r') as f1:
            with open(path2, 'r') as f2:

                writer = csv.writer(f0)
                reader1 = csv.reader(f1)
                reader2 = csv.reader(f2)

                header = next(reader1)
                next(reader2)    # skip header in file 2; same as in file 1

                writer.writerow(header)     # write original header to output file

                # Using next() lazily loads each line of the file.
                row1 = next(reader1, None)  # fall back to None value when file is empty
                row2 = next(reader2, None)

                while row1 is not None and row2 is not None:
                    # Append the earliest log to output file.
                    if is_earlier(row1, row2):
                        writer.writerow(row1)
                        row1 = next(reader1, None)
                    else:
                        writer.writerow(row2)
                        row2 = next(reader2, None)

                # Write the remaining rows to the output file.
                if row1 is not None or row2 is not None:
                    if row1 is None:
                        writer.writerow(row2)
                        writer.writerows(reader2)
                    elif row2 is None:
                        writer.writerow(row1)
                        writer.writerows(reader1)

    return out_path


def merge_dir(directory: str = "data", out_path: str = "merged_log.csv"):
    """Merge all individually sorted log files in a directory to a single sorted log file."""
    paths = sorted(glob.glob(f"{directory}/*.csv"))
    if not paths:
        raise ValueError(f"No files found in {directory}")

    file_num = 0

    def recurse(r_paths):
        if len(r_paths) <= 1:
            return r_paths[0]
        else:
            nonlocal file_num

            q = len(r_paths) // 2
            a = recurse(r_paths[:q])
            b = recurse(r_paths[q:])

            merged_path = merge(a, b, f"temp{file_num}_{out_path}")
            file_num += 1

            if a.startswith("temp"):
                os.remove(a)
            if b.startswith("temp"):
                os.remove(b)

            return merged_path

    # Recursively merge the files.
    merged_path = recurse(paths)

    # Rename the resultant file to the correct output path.
    if os.path.exists(out_path):
        os.remove(out_path)
    os.rename(merged_path, out_path)


if __name__ == "__main__":
    merge_dir()
