This project was developed as part of the CMPSC 463 – Design and Analysis of Algorithms course at Penn State Abington. The project report can be found below, and the instructions & requirements for the project can be found in [`instr.md`](instr.md).

To run the programs, clone the repository and set up an environment with Numpy installed (`pip install numpy`). Each part of the project is self-contained in a separate Python file that can each be run directly.

# Divide-and-Conquer Algorithms on Distributed System Logs

## 1. Project Description

The objective of this project is to apply divide-and-conquer algorithms to the analysis of distributed system logs. The dataset contains six chronologically-sorted CSV files derived from Hadoop system logs (findable [here](https://drive.google.com/file/d/1u2AepGDEyyE2s51BM2Q7v9Xf0jwOp50n/view?usp=sharing)). Each file represents a separate system component and stores related information including timestamps, component names, event identifiers, and log messages.

The project is divided into three main tasks. First, a distributed K-way log stream merger combines the six files into a single chronological log file using a recursive two-way merging strategy. Lazy loading is used to avoid loading entire files into memory during the merging process. Second, a component dependency matrix is constructed from the merged log, and Strassen's matrix multiplication algorithm is used to calculate two-hop and three-hop component relationships. Finally, a divide-and-conquer burst detection algorithm identifies periods of concentrated log activity based on the number of events and the time span between them.

Expected outcomes include a globally sorted log file, dependency matrices representing relationships among system components, and a list of detected bursts. In this report, toy examples and experiments with the provided dataset are used to examine the correctness and behavior of the algorithms.

## 2. Algorithms

### 2.1. Distributed K-Way Log Stream Merger Using Divide-and-Conquer

- **2.1.1. Algorithm Definition**

    - **Input:** A directory containing six CSV log files, each individually chronologically sorted.

    - **Output:** A single file named `merged_log.csv` containing all input log entries in chronological order.

    - **Problem Statement:** The input files are individually sorted, but their contents must be combined into a single sorted output file. The objective is to merge the files efficiently without loading all their contents into memory at once.

- **2.1.2. Divide-and-Conquer Design**

    <!-- - **Recursive Strategy**: The algorithm will create a list of all files stored in an input directory, then recursively divide the collection into two approximately equal groups. Each group will be recursively merged until all files have been reduced to a single sorted stream. -->

    - **Base Case:** If the recursive input contains only a single file, return the file.

    - **Divide:** Divide the collection of file paths into two approximately equal groups.

    - **Conquer:** Recursively merge each group until each group has been reduced to a single sorted stream.

    - **Combine:** Perform a two-way merge of the two resulting streams. Compare their current timestamps, write the earlier entry to the output, and read the next entry from that stream. Continue until both streams are exhausted.

    The process repeats until all files have been combined into one globally sorted file.

    Lazy loading is implemented by reading one current row from each input stream at a time. After a row is written to the output, another row is read from the corresponding stream. This reduces the amount of input data held in memory during merging.

**Pseudocode:**

```text
MergeDirectory(files):
    if files is empty:
        report an error

    if files contains one file:
        return that file

    divide files into left and right groups

    left_result  = MergeDirectory(left)
    right_result = MergeDirectory(right)

    return Merge(left_result, right_result)

Merge(file1, file2):
    read the header from each file
    write one header to the output

    read the first data row from each file

    while both streams contain rows:
        if timestamp(row1) <= timestamp(row2):
            write row1
            read the next row from file1
        else:
            write row2
            read the next row from file2

    write all remaining rows from either stream

    return the merged output file
```

The two-way merge takes linear time in the number of entries being merged. The overall merging time is `O(n * log(k))` when each merge pass processes all entries, where `n` is the total number of log entries and `k` is the number of input files. The recursive merging structure also ensures that each individual merge operates on two sorted streams.

### 2.2. Strassen's Algorithm for Square Matrix Multiplication of Arbitrary Size

- **2.2.1. Algorithm Definition**

    - **Input:** A square component dependency matrix `A`.

    - **Output:** The products `A^2` and `A^3`.

    - **Problem Statement:** The dependency matrix represents transitions between system components. An entry `A[i,j]=1` indicates that an event from component `j` immediately follows an event from component `i` at least once in the merged log. An entry of zero indicates that this transition was not observed.
    The objective is to identify paths consisting of two and three transitions by calculating `A^2 = A * A` and `A^3 = A^2 * A`. Strassen's algorithm is used to perform the matrix multiplications recursively.

- **2.2.2. Divide-and-Conquer Design**

    - **Base Case:** If the matrices contain a single element, multiply and return their elements.

    - **Divide:** Split each matrix into four equally-sized submatrices (eight total): 

        ```
        A = [[A, B],
             [C, D]]
        B = [[E, F],
             [G, H]]
        ```

    - **Conquer:** Recursively calculate seven products:

        ```
        P1 = A (F - H)
        P2 = (A + B) H
        P3 = (C + D) E
        P4 = D (G - E)
        P5 = (A + D)(E + H)
        P6 = (B - D)(G + H)
        P7 = (A - C)(E + F)
        ```

    - **Combine:** Calculate and combine the four output submatrices:

        ```
        C11 = (P5 + P4 + P6) - P2
        C12 = P1 + P2
        C21 = P3 + P4
        C22 = (P1 + P5) - (P3 + P7)

        OUT = [[C11, C12],
               [C21, C22]]
        ```

    Because Strassen's algorithm is implemented most conveniently for dimensions that are powers of two, the implementation pads matrices with zeros until their dimensions reach the next power of two. After multiplication, the added rows and columns are removed. This allows the algorithm to operate on square matrices of arbitrary positive dimensions.

**Pseudocode:**

```text
Strassen(A, B):

    if dimensions of A = 1x1:
        return A[0,0] * B[0,0]

    divide A and B into four submatrices each

    calculate P1 through P7 recursively using Strassen's formulae

    calculate C11, C12, C21, C22

    combine the four submatrices into OUT

    return OUT

StrassenArbitrarySize(A, B):
    pad A and B with zeros to the next power of two
    MULT = Strassen(padded_A, padded_B)
    remove the padded rows and columns from MULT
    return MULT
```

Strassen's algorithm has a theoretical time complexity of approximately `O(n^(log_b2(3)))`, compared with `O(n^3)` for conventional matrix multiplication. The implementation uses this algorithm for both `A^2` and `A^3`.

### 2.3. Divide-and-Conquer Burst Detection

- **2.3.1. Algorithm Definition**

    - **Input:** A chronologically sorted log file, a minimum event count `M`, a time threshold `T`, and a base-case size `B`.

    - **Output:** The total number of detected non-overlapping bursts and a list containing the details of each burst.

    - **Problem Statement:** A burst is a concentrated region of log activity containing at least `M` events within a time span shorter than `T`. The algorithm must identify these regions while using recursively finding bursts in partitioned halves and checking for bursts that cross partition boundaries.
        - The time span is defined as: `span = max(timestamps) - min(timestamps)`
        - A group qualifies when: `num_events >= M && span < T`

- **2.3.2. Divide-and-Conquer Design**

    - **Base Case:** When a partition contains at most `B` entries, examine the events directly to identify qualifying windows of `M` consecutive events.

    - **Divide:** Split the sorted timeline into two approximately equal partitions using the median index.

    - **Conquer:** Recursively identify candidate burst windows in each partition.

    - **Combine:** Examine windows of M consecutive events that cross the median. If their timestamps span less than `T`, they are also qualifying candidates. The final processing step greedily combines candidates into non-overlapping bursts.
Rather than returning burst counts directly from each recursive call, the implementation returns candidate starting indices from recursive calls and constructs the final non-overlapping burst list after all recursion has finished.

**Pseudocode:**

```text
FindCandidates(start, end):
    if partition contains at most B entries:
        find all qualifying M-event windows
        return their starting indices

    divide partition at midpoint

    left_candidates  = FindCandidates(left partition)
    right_candidates = FindCandidates(right partition)

    candidates = union(left_candidates, right_candidates)

    examine M-event windows crossing the median
    add qualifying crossing windows to candidates

    return candidates

CandidatesToBursts(log):
    candidates = FindCandidates(log)

    bursts = empty list

    process candidates in chronological order:
        extend each selected burst to the latest event whose timestamp 
            is less than T from its start
        record the burst
        skip events assigned to that burst

    return number of bursts, bursts
```

The implementation uses a greedy non-overlapping convention: Each selected burst begins at the earliest remaining qualifying candidate and includes as many subsequent events as possible without violating the time threshold. The next burst begins after the selected burst ends. This convention prevents events from being assigned to multiple reported bursts.


## 3. Verification with Toy Examples

### 3.1. Distributed K-Way Log Stream Merger

Consider three input streams containing timestamps:

- Stream A: 01
- Stream B: 02
- Stream C: 05
- Stream D: 03, 04

Each stream is already sorted. The merger recursively divides the streams into groups, merges each group, and finally combines the results.

The expected merged output is:

```text
01, 02, 03, 04, 05
```

Tracing the pseudocode:

```text
MergeDirectory(A, B, C, D)
    left = MergeDirectory(A, B)
        left = A
        right = B
        Merge(A, B)
            O = output file
            A[0] = 01 < B[0] = 02
            write 01 to O, pop A[0]
            A is empty
            write remaining of B to O
        => 01, 02
    right = MergeDirectory(C, D)
        left = C
        right = D
        Merge(C, D)
            O = output file
            C[0] = 05 > D[0] = 03
            write 03 to O, pop D[0]
            C[0] = 05 > D[0] = 04
            write 04 to O, pop D[0]
            D is empty
            write remaining of C to O
        => 03, 04, 05
    Merge(left, right)
        O = output file
        left[0] = 01 < right[0] = 03
        write 01 to O, pop left[0]
        left[0] = 02 < right[0] = 03
        write 02 to O, pop left[0]
        left is empty
        write remaining of right to O
    => 01, 02, 03, 04, 05
```

Every input entry appears exactly once, and the resulting stream is chronologically sorted. This demonstrates that merging individually sorted streams can produce one globally sorted stream without sorting all entries from scratch.

### 3.2. Fault Dependency Analysis Using Strassen's Matrix Multiplication

Consider three components, A, B, and C, with the merged event sequence:

```text
A → B → C
```

The corresponding binary dependency matrix is:

```text
A = [[0, 1, 0],
     [0, 0, 1],
     [0, 0, 0]]
```

The two-hop dependency matrix is:

```text
A^2 = [[0, 0, 1],
       [0, 0, 0],
       [0, 0, 0]]
```

The entry at row A, column C is 1 because there is a two-transition path from A to C through B.

The three-hop dependency matrix is:

```text
A^3 = [[0, 0, 0],
       [0, 0, 0],
       [0, 0, 0]]
```

There are no paths containing exactly three transitions in this example. The results illustrate how matrix multiplication identifies indirect relationships between components.

To obtain A^2, we multiply A by itself with Strassen's algorithm. In this project's implementation, since the size of A is 3, not a power of 2, it will be padded with one row and column of 0s to bring the size to 4, the smallest next power of 2:

```text
A_pad = [[0, 1, 0, 0],
         [0, 0, 1, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0]]
```


### 3.3. Divide-and-Conquer Burst Detection

Consider these event timestamps, measured in seconds: `0.0, 0.2, 0.4, 0.8, 1.3, 1.7`

Let `M = 3` and `T = 1 second`.

The timestamps are divided into two groups at the midpoint. The first group A contains events at `0.0`, `0.2`, and `0.4` seconds. Its span is `0.4` seconds and contains at least 3 elements, so it qualifies as a burst.

The second group B contains events at `0.8`, `1.3`, and `1.7` seconds. Its span is `0.9` seconds and also contains at least 3 elements, so it also qualifies as a burst.

The candidate bursts across the median must also be detected. Groups of `M` size that span the median are created. The first group C is `0.2, 0.4, 0.8`, whose span is `0.6`, so it is a burst. The second group D is `0.4, 0.8, 1.3`, whose span is 0.9, so it is also a burst.

All candidate bursts are then iterated through and merged to remove overlapping regions. 
Groups A and C contain overlapping bursts, so a burst region is created to contain all timestamps that don't exceed a span of `T`: `0.0, 0.2, 0.4, 0.8`. The remaining timestamps are part of both groups B and D, and their total span is less than `T`, so another burst region is created: `1.3, 1.7`.

Thus, this example results in two detected bursts: `0.0, 0.2, 0.4, 0.8` and `1.3, 1.7`.


## 4. Numerical Experiments Using the Target Dataset

### 4.1. Distributed K-Way Log Stream Merger

The six input log files were merged into `merged_log.csv` using the recursive K-way merge implementation. Each merge operation reads the next required entry from its input streams rather than loading the entire files into memory. The first and last twenty rows of the resultant `merged_log.csv` are shown below.

![First 20 rows of `merged_log.csv`](outputs/first20merged.png)
![Last 20 rows of `merged_log.csv`](outputs/last20merged.png)

The resultant file contains every original log entry exactly once and is sorted by timestamp. [`merged_log.csv`](outputs/merged_log.csv) is contained in this directory for independent verification of chronological ordering and total entries.

### 4.2. Fault Dependency Analysis Using Strassen's Matrix Multiplication

The component dependency matrix was constructed by scanning consecutive entries in the merged log. Each distinct component was assigned a matrix index, and each observed transition was recorded as a binary entry.

**Dependency matrix A:** 
```text
[[1. 1. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 1. 1. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1.]
 [0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [1. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 1. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 1. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 1. 1. 0. 1. 1. 0. 1. 1. 1. 1. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 1. 1. 0. 0. 0. 1. 1. 1. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 1. 0. 0. 1. 0. 1. 1. 0. 0. 0.]
 [0. 0. 0. 1. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 1. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 1. 1. 1. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 0. 1. 1. 1. 0. 1. 0. 0. 0. 0.]
 [0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 1. 1. 0. 1. 1. 1. 1. 0. 1. 1. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 1. 0. 0. 0. 0. 0. 0. 1. 1. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 1. 1. 0. 0. 0. 0. 1. 1. 1. 1. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 1. 0. 0. 1. 0. 1. 1. 1. 1. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 1. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 1. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]]
```

**Two-hop dependency matrix A^2:** 
```text
[[1. 2. 1. 0. 1. 0. 0. 1. 1. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 1. 2. 1. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 1. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1.]
 [0. 1. 1. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 2. 0. 1. 1. 0. 1. 1. 0. 1. 1. 1. 1. 0. 0. 0.]
 [0. 0. 0. 0. 0. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [1. 0. 0. 0. 0. 1. 2. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0.]
 [2. 1. 0. 1. 0. 0. 2. 1. 0. 0. 0. 0. 0. 0. 0. 0. 2. 0. 3. 1. 0. 2. 3. 1. 3. 1. 1. 2. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 1. 0. 0. 0. 1. 1. 1. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 1. 1. 2. 1. 0. 1. 0. 0. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 1. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 1. 1. 1. 2. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 2. 1. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 0. 0. 0. 0. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 1. 0. 1. 0. 0. 0. 0. 0. 0. 1. 2. 0. 2. 1. 0. 0. 1. 2. 1. 0. 1. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 2. 1. 0. 1. 0. 0. 0. 0. 2. 1. 2. 1. 0. 1. 1. 0. 1. 1. 1. 1. 0. 0. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 1. 1. 0. 1. 1. 0. 1. 1. 1. 1. 0. 0. 0.]
 [0. 0. 0. 2. 0. 0. 1. 0. 1. 0. 0. 0. 0. 0. 0. 2. 6. 0. 7. 4. 1. 3. 3. 2. 7. 4. 6. 5. 1. 1. 0.]
 [0. 0. 0. 1. 0. 0. 1. 0. 1. 0. 0. 0. 0. 0. 0. 2. 4. 0. 4. 4. 1. 2. 1. 1. 4. 3. 5. 3. 0. 0. 0.]
 [1. 0. 0. 2. 0. 0. 2. 0. 0. 0. 0. 0. 0. 0. 0. 2. 3. 0. 4. 3. 1. 3. 2. 1. 5. 2. 4. 4. 1. 1. 0.]
 [1. 1. 0. 1. 0. 0. 1. 0. 1. 0. 0. 0. 0. 0. 0. 1. 1. 0. 5. 1. 0. 3. 2. 1. 2. 0. 2. 2. 1. 1. 1.]
 [0. 0. 0. 1. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 1. 1. 0. 4. 3. 0. 2. 4. 3. 4. 1. 3. 2. 0. 0. 0.]
 [1. 0. 0. 1. 0. 0. 2. 0. 0. 0. 0. 0. 0. 0. 0. 2. 3. 0. 6. 5. 1. 3. 5. 3. 6. 3. 5. 3. 0. 0. 0.]
 [0. 1. 0. 2. 0. 0. 2. 0. 0. 0. 0. 0. 0. 0. 0. 3. 5. 0. 7. 5. 1. 3. 4. 4. 8. 3. 6. 5. 1. 1. 1.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 1. 4. 0. 4. 2. 0. 1. 1. 0. 2. 3. 3. 2. 0. 0. 0.]
 [0. 0. 0. 1. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 3. 6. 0. 6. 4. 1. 3. 2. 2. 5. 4. 6. 4. 1. 1. 0.]
 [0. 0. 0. 2. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 2. 3. 0. 5. 3. 0. 3. 2. 1. 5. 2. 5. 7. 1. 3. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 2. 0. 3. 2. 0. 2. 1. 0. 3. 2. 3. 4. 1. 2. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 1. 0. 0. 1. 0. 1. 2. 1. 2. 0.]
 [0. 0. 0. 0. 0. 0. 0. 0. 1. 0. 0. 0. 0. 0. 0. 0. 1. 0. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]]
```

**Three-hop dependency matrix A^3:** 
```
[[ 1.  3.  3.  1.  2.  1.  0.  1.  2.  1.  0.  1.  0.  0.  0.  2.  1.  1.  0.  0.  0.  0.  0.  1.  0.  0.  0.  0.  0.  0.  0.]
 [ 0.  2.  3.  2.  1.  2.  1.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  1.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  1.]
 [ 0.  2.  2.  1.  1.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  2.  0.  2.  1.  0.  1.  1.  0.  1.  1.  1.  1.  0.  0.  1.]
 [ 0.  1.  2.  3.  1.  1.  1.  0.  2.  0.  0.  0.  0.  0.  0.  2.  7.  0.  8.  4.  1.  3.  3.  2.  7.  4.  6.  5.  1.  1.  0.]
 [ 1.  0.  0.  0.  0.  1.  2.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  1.  0.  0.  1.  1.  0.  0.  0.  0.  0.  0.  0.  0.]
 [ 3.  1.  0.  1.  0.  1.  4.  1.  0.  0.  0.  0.  0.  0.  0.  0.  2.  0.  4.  1.  0.  3.  4.  1.  3.  1.  1.  2.  0.  0.  0.]
 [ 4.  4.  1.  5.  1.  0.  5.  2.  3.  0.  0.  0.  0.  0.  0.  5. 10.  0. 19.  9.  1. 10. 12.  7. 16.  6. 12. 11.  2.  2.  1.]
 [ 0.  0.  0.  0.  0.  0.  1.  0.  2.  1.  1.  2.  1.  0.  1.  1.  2.  1.  3.  1.  0.  0.  1.  2.  1.  0.  1.  0.  0.  0.  0.]
 [ 0.  0.  0.  0.  0.  0.  0.  1.  2.  1.  1.  3.  2.  1.  3.  0.  1.  1.  2.  1.  0.  1.  1.  0.  1.  1.  1.  1.  0.  0.  0.]
 [ 0.  0.  0.  0.  0.  0.  0.  0.  1.  1.  0.  1.  0.  0.  0.  0.  0.  1.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.]
 [ 0.  0.  0.  0.  0.  0.  0.  0.  1.  1.  1.  2.  1.  0.  1.  0.  0.  1.  1.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.]
 [ 0.  0.  0.  0.  0.  0.  0.  2.  1.  0.  0.  2.  1.  2.  3.  1.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.]
 [ 0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  2.  1.  1.  1.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.]
 [ 0.  0.  0.  0.  0.  0.  0.  1.  0.  0.  0.  3.  2.  2.  3.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.  0.]
 [ 0.  0.  0.  0.  0.  0.  0.  1.  2.  1.  0.  1.  0.  0.  1.  2.  1.  1.  0.  0.  0.  0.  0.  1.  0.  0.  0.  0.  0.  0.  0.]
 [ 1.  0.  0.  1.  0.  0.  3.  0.  3.  1.  0.  1.  0.  0.  0.  3.  7.  1. 10.  7.  1.  4.  7.  5.  8.  4.  7.  4.  0.  0.  0.]
 [ 0.  0.  0.  2.  0.  0.  1.  0.  4.  2.  1.  3.  1.  0.  1.  2.  8.  2. 10.  5.  1.  4.  4.  2.  8.  5.  7.  6.  1.  1.  0.]
 [ 0.  0.  0.  2.  0.  0.  1.  0.  1.  0.  0.  0.  0.  0.  0.  2.  6.  0.  7.  4.  1.  3.  3.  2.  7.  4.  6.  5.  1.  1.  0.]
 [ 1.  2.  0. 10.  0.  0.  7.  0.  7.  1.  0.  1.  0.  0.  0. 15. 32.  1. 44. 27.  4. 21. 20. 14. 38. 21. 37. 31.  5.  7.  2.]
 [ 1.  1.  0.  6.  0.  0.  5.  0.  5.  1.  0.  1.  0.  0.  0. 11. 24.  1. 27. 19.  4. 13. 11.  8. 25. 16. 25. 19.  3.  3.  1.]
 [ 3.  3.  0.  8.  0.  0.  7.  1.  3.  0.  0.  0.  0.  0.  0. 11. 21.  0. 30. 18.  3. 16. 14. 10. 27. 13. 25. 23.  4.  6.  2.]
 [ 2.  3.  1.  5.  1.  0.  5.  1.  2.  1.  0.  1.  0.  0.  0.  5. 14.  1. 18. 11.  1. 10. 11.  6. 18.  8. 14. 16.  2.  4.  1.]
 [ 1.  1.  0.  6.  0.  0.  6.  0.  1.  0.  0.  0.  0.  0.  0.  8. 15.  0. 24. 17.  3. 11. 16. 12. 25. 11. 20. 15.  2.  2.  1.]
 [ 3.  2.  0.  9.  0.  0.  9.  1.  3.  0.  0.  0.  0.  0.  0. 13. 27.  0. 37. 26.  5. 18. 22. 16. 37. 19. 32. 24.  3.  3.  1.]
 [ 2.  3.  1. 11.  1.  0. 10.  0.  5.  0.  0.  0.  0.  0.  0. 17. 33.  0. 47. 31.  5. 23. 25. 19. 43. 21. 40. 32.  5.  7.  2.]
 [ 0.  0.  0.  3.  0.  0.  1.  0.  5.  1.  0.  1.  0.  0.  0.  6. 18.  1. 19. 11.  2.  8.  7.  4. 15. 12. 16. 12.  2.  2.  0.]
 [ 0.  1.  0.  8.  0.  0.  6.  0.  7.  1.  0.  1.  0.  0.  0. 14. 32.  1. 37. 24.  4. 16. 15. 12. 33. 20. 33. 27.  4.  6.  1.]
 [ 1.  2.  0.  8.  0.  0.  5.  0.  3.  0.  0.  0.  0.  0.  0. 12. 23.  0. 34. 19.  3. 18. 14. 10. 31. 15. 29. 29.  7. 11.  2.]
 [ 0.  0.  0.  5.  0.  0.  2.  0.  2.  0.  0.  0.  0.  0.  0.  7. 15.  0. 19. 11.  2. 10.  7.  5. 18. 10. 18. 18.  4.  7.  0.]
 [ 0.  0.  0.  2.  0.  0.  1.  0.  0.  0.  0.  0.  0.  0.  0.  2.  3.  0.  6.  3.  0.  4.  2.  1.  6.  2.  6.  9.  2.  5.  0.]
 [ 0.  0.  0.  0.  0.  0.  0.  0.  2.  1.  0.  1.  0.  0.  0.  0.  2.  1.  2.  1.  0.  1.  1.  0.  1.  1.  1.  1.  0.  0.  0.]]
```

The matrices `A^2` and `A^3` were checked against Numpy's matrix multiplication on the same inputs to verify the implementation--both methods returned the same result. The resulting matrices may contain values greater than 1 because ordinary matrix multiplication counts paths rather than merely recording whether a path exists.

### 4.3. Divide-and-Conquer Burst Detection

Burst detection was evaluated using six combinations of time threshold `T` and minimum event count `M`. The base-case size was kept fixed at `B = 5` and the experiment re-run with `B = 10` to verify that the results were not impacted. A summary table of the results is below, with the full output of `part3.py` further down.

| Case | M | T | Bursts detected |
|---|---:|---:| ---:|
| 1 | 10 | 0.5s | 18 |
| 2 | 10 | 1s | 20 |
| 3 | 10 | 2s | 22 |
| 4 | 20 | 0.5s | 4 |
| 5 | 20 | 1s | 7 |
| 6 | 20 | 2s | 13 |

The total number of bursts and the number of events included in those bursts were recorded for each configuration. As would be expected, increasing the maximum timespan `T` of a qualifying burst consistently increased the number of bursts detected, and increasing the minimum number of events `M` decreased teh number of bursts detected.

Full output of `part3.py`:
```text
Case 1: m = 10, t = 0.5s
	18 bursts were found in the data.
	Timespan: 0:00:00.453000 | Number of logs: 15
	Timespan: 0:00:00.485000 | Number of logs: 12
	Timespan: 0:00:00.282000 | Number of logs: 12
	Timespan: 0:00:00.485000 | Number of logs: 60
	Timespan: 0:00:00.375000 | Number of logs: 16
	Timespan: 0:00:00.047000 | Number of logs: 16
	Timespan: 0:00:00.078000 | Number of logs: 16
	Timespan: 0:00:00.344000 | Number of logs: 15
	Timespan: 0:00:00.187000 | Number of logs: 16
	Timespan: 0:00:00.438000 | Number of logs: 13
	Timespan: 0:00:00.343000 | Number of logs: 17
	Timespan: 0:00:00.250000 | Number of logs: 18
	Timespan: 0:00:00.297000 | Number of logs: 18
	Timespan: 0:00:00.391000 | Number of logs: 17
	Timespan: 0:00:00.391000 | Number of logs: 10
	Timespan: 0:00:00.390000 | Number of logs: 12
	Timespan: 0:00:00.141000 | Number of logs: 24
	Timespan: 0:00:00.156000 | Number of logs: 23

Case 2: m = 10, t = 1s
	20 bursts were found in the data.
	Timespan: 0:00:00.969000 | Number of logs: 19
	Timespan: 0:00:00.469000 | Number of logs: 21
	Timespan: 0:00:00.985000 | Number of logs: 16
	Timespan: 0:00:00.156000 | Number of logs: 48
	Timespan: 0:00:00.531000 | Number of logs: 21
	Timespan: 0:00:00.047000 | Number of logs: 16
	Timespan: 0:00:00.078000 | Number of logs: 16
	Timespan: 0:00:00.344000 | Number of logs: 15
	Timespan: 0:00:00.953000 | Number of logs: 29
	Timespan: 0:00:00.343000 | Number of logs: 17
	Timespan: 0:00:00.953000 | Number of logs: 19
	Timespan: 0:00:00.984000 | Number of logs: 11
	Timespan: 0:00:00.969000 | Number of logs: 19
	Timespan: 0:00:00.906000 | Number of logs: 15
	Timespan: 0:00:00.922000 | Number of logs: 10
	Timespan: 0:00:00.875000 | Number of logs: 14
	Timespan: 0:00:00.641000 | Number of logs: 14
	Timespan: 0:00:00.968000 | Number of logs: 13
	Timespan: 0:00:00.078000 | Number of logs: 16
	Timespan: 0:00:00.156000 | Number of logs: 23

Case 3: m = 10, t = 2s
	22 bursts were found in the data.
	Timespan: 0:00:01.843000 | Number of logs: 18
	Timespan: 0:00:01.531000 | Number of logs: 27
	Timespan: 0:00:01.453000 | Number of logs: 66
	Timespan: 0:00:01.593000 | Number of logs: 23
	Timespan: 0:00:01.047000 | Number of logs: 19
	Timespan: 0:00:01.093000 | Number of logs: 19
	Timespan: 0:00:01.844000 | Number of logs: 15
	Timespan: 0:00:01.735000 | Number of logs: 11
	Timespan: 0:00:01.703000 | Number of logs: 30
	Timespan: 0:00:01.203000 | Number of logs: 27
	Timespan: 0:00:01.516000 | Number of logs: 11
	Timespan: 0:00:01.984000 | Number of logs: 23
	Timespan: 0:00:01.141000 | Number of logs: 12
	Timespan: 0:00:01.360000 | Number of logs: 35
	Timespan: 0:00:01.969000 | Number of logs: 21
	Timespan: 0:00:01.953000 | Number of logs: 10
	Timespan: 0:00:01.718000 | Number of logs: 10
	Timespan: 0:00:01.891000 | Number of logs: 13
	Timespan: 0:00:01.797000 | Number of logs: 24
	Timespan: 0:00:01.984000 | Number of logs: 17
	Timespan: 0:00:01.047000 | Number of logs: 20
	Timespan: 0:00:01.016000 | Number of logs: 27

Case 4: m = 20, t = 0.5s
	4 bursts were found in the data.
	Timespan: 0:00:00.469000 | Number of logs: 21
	Timespan: 0:00:00.485000 | Number of logs: 60
	Timespan: 0:00:00.141000 | Number of logs: 24
	Timespan: 0:00:00.156000 | Number of logs: 23

Case 5: m = 20, t = 1s
	7 bursts were found in the data.
	Timespan: 0:00:00.891000 | Number of logs: 25
	Timespan: 0:00:00.500000 | Number of logs: 62
	Timespan: 0:00:00.531000 | Number of logs: 21
	Timespan: 0:00:00.953000 | Number of logs: 29
	Timespan: 0:00:00.937000 | Number of logs: 20
	Timespan: 0:00:00.907000 | Number of logs: 25
	Timespan: 0:00:00.156000 | Number of logs: 23

Case 6: m = 20, t = 2s
	13 bursts were found in the data.
	Timespan: 0:00:01.735000 | Number of logs: 40
	Timespan: 0:00:01.172000 | Number of logs: 64
	Timespan: 0:00:01.593000 | Number of logs: 23
	Timespan: 0:00:01.547000 | Number of logs: 22
	Timespan: 0:00:01.969000 | Number of logs: 20
	Timespan: 0:00:01.703000 | Number of logs: 30
	Timespan: 0:00:01.203000 | Number of logs: 27
	Timespan: 0:00:01.984000 | Number of logs: 23
	Timespan: 0:00:01.703000 | Number of logs: 26
	Timespan: 0:00:01.547000 | Number of logs: 26
	Timespan: 0:00:01.968000 | Number of logs: 23
	Timespan: 0:00:01.078000 | Number of logs: 29
	Timespan: 0:00:01.187000 | Number of logs: 27
```


## 5. Discussion

### 5.1. Discussion of Distributed K-Way Log Stream Merger Results

The K-way merge algorithm combines the six chronologically sorted input files through a sequence of recursive two-way merges. Because the input streams are already sorted, each merge operation only needs to compare the next available timestamps instead of sorting every entry from scratch.

Lazy loading reduced the amount of input data held in memory during each merge. Rather than reading entire files into memory, the algorithm maintains the current row from each input stream and reads additional entries as needed.

### 5.2. Discussion of Using Strassen's Matrix Multiplication

The dependency matrix provided a representation of transitions observed between system components in the merged log. Its binary entries indicate whether a particular transition was observed, regardless of how many times it occurred.

The products A^2 and A^3 extend this analysis to paths containing two and three transitions, respectively. These products can reveal indirect relationships that are not necessarily represented by a direct transition in the original matrix.

Strassen's algorithm provides a lower time complexity than naive matrix multiplication and reduces the number of recursive matrix multiplications compared with conventional divide-and-conquer multiplication. Padding the matrices to a power-of-two dimension allows the recursive algorithm to handle component counts that do not naturally fit its splitting structure. However, it should be noted that the time complexity of Strassen multiplication is only slightly faster than the naive approach (appx. O(n^2.8) vs O(n^3), respectively), meaning that the overhead of recursion will make Strassen multiplication slower for relatively smaller sizes of matrices.

The main implementation challenge was correctly padding the matrix for non–power-of-two–dimension matrices. Strassen multiplication works most effectively when the matrix at each recursive call can be divided exactly in half. This was achieved by padding the dimensions of the matrix with 0s before Strassen multiplication, then removing this padding after calculation was finished. It was also important to ensure that the seven recursive products and their recombination formulas are correct, and that the final output matched a known standard implementation of matrix multiplication. Comparing the results against conventional Numpy matrix multiplication provided a practical correctness check, revealing that the implementation produced the correct result.

### 5.3. Discussion of Divide-and-Conquer Burst Detection Results

The burst detection experiments examine how the time threshold `T` and minimum event count `M` influence the detection of concentrated log activity.

Increasing `T` allows events spread over a longer interval to qualify as a burst, while decreasing `T` requires events to occur closer together. Increasing `M` makes the detection criterion stricter because more events must occur within the permitted time span.

The six experiments allowed these effects to be compared by changing one parameter at a time. For example—cases 1—3 keep `M` fixed while varying `T`, and cases 4—6 repeat the comparison with a larger `M`.

The recursive division reduces the size of each partition until the base-case limit is reached. The combine step is important because a qualifying burst may contain events from both sides of a partition boundary. Failing to check these events would cause some or many bursts to be passed over.

The reported number of bursts depends on not only the thresholds, but also the rule(s) used to combine overlapping groups of bursts. This implementation applies a greedy non-overlapping convention when converting candidate windows into final bursts.

As discussed in section 4.3, the total number of bursts and the number of events included in those bursts were recorded for each configuration. As would be expected, increasing the maximum timespan `T` of a qualifying burst consistently increased the number of bursts detected, and increasing the minimum number of events `M` decreased teh number of bursts detected. A table of the results can be found in section 4.3.

## 6. Conclusions

### 6.1. Key Lessons Learned

This project demonstrates how divide-and-conquer algorithms can be applied to different types of distributed log analysis.

The K-way merger illustrates how a large collection of sorted data streams can be combined efficiently through recursive two-way merging. Lazy loading provides an additional memory-efficiency benefit by reading entries only when they are needed.

Strassen's matrix multiplication demonstrates how recursive matrix operations can reduce the number of multiplications required compared with conventional matrix multiplication. Applying this algorithm to the component dependency matrix makes it possible to examine two-hop and three-hop paths through the observed system transition network.

The burst detection algorithm demonstrates how a timeline can be divided into smaller intervals while still identifying patterns that cross partition boundaries. Its correctness depends on consistently applying the time-span and minimum-event-count conditions, as well as avoiding duplicate counts when constructing non-overlapping bursts.

Together, the three algorithms illustrate that divide and conquer is not limited to one type of problem and is can be useful in practice. As shown in this project, it can be applied to stream merging, matrix computation, and temporal pattern detection, provided that each algorithm has a well-defined structure, including a base case and a correct combine step.

### 6.2. Challenges Encountered

One challenge was preserving chronological order while merging multiple files without loading their complete contents into memory. The recursive merging structure and lazy reading approach address this challenge, although intermediate file management and repeated timestamp parsing require attention.

A second challenge was implementing Strassen's algorithm correctly for matrices whose dimensions are not powers of two. Padding the matrices and removing the extra rows and columns provides a general solution, but the recursive multiplication formulae must be implemented carefully and verified against an independent reference calculation.

The burst detection algorithm presented a different challenge: A burst can cross the midpoint of a recursive partition, and overlapping qualifying windows can represent the same region of activity. The biggest challenge of the implementation was deciding how to handle overlapping groups of bursts. Ultimately, the implementation uses a greedy convention to produce non-overlapping bursts. Defining this convention clearly was necessary for consistent results.

Finally, evaluating the algorithms on the complete dataset required checking correctness in addition to recording numerical outputs. Comparing input and output entry counts, verifying chronological ordering, validating matrix products, and inspecting detected bursts help to ensure that the results reflect the intended algorithm definitions.
