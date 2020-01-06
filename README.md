# NFV parallelism placment

Jointly consider placement and parallelism of VNF.

## TODO

Some todo tips.

### LP part

* Remove the latency constraints in program. (It is not written in the paper)

### LP-based Heuristic

* The precedure of **configuration** generation is too slow. Analysis every
small step of configuration:
  1. Permute the available servers (sorted by computing resources);
     * using python permuation lib
  2. For each permutation:
     1. generate routes: 
        * BFS between each pair; (this can be optimized by pre computing)
     2. generate configurations (**intensively time-consuming**, this can
     also be pre computed)
        * using queue.
        * irrelative with concrete server.
  3. Keep generate configurations until its size reaches K. (Note: K is
  folded after each iteration.)

  how to ensure the first K configurations generated are the optimal

* **Analysis** the algorithm, including the performance bound, NP-hardness, etc.

  * ICDCS17：
    * Jackson network: queueing network
    * NP-hard: bin packing problem
    * near optimal

### Greedy

* Need to design a more **enlightening** greedy algorithm, taking parallelism
into consideration.

## Reference

[python风格规范](https://zh-google-styleguide.readthedocs.io/en/latest/google-python-styleguide/python_style_rules/)
