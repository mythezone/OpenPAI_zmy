# TSP demo with TCP communication (step 1)

## How to use:
1. Run the `test_master.py`,`test_loop.py`,`test_iteration.py` and `test_init.py` file in a row.
2. The `test_loop.py` program will give the final result.

## Problems remain to solve:
1. ~~The socket cannot sent message larger than 1024(maybe more,but still not enough) Byte, so the scala of the TCP problem cannot be large. In fact, in this demo I choose a little sample with 10 cities.~~ This problem has been solved.
2. The ports in this program are setted artibrarily, and should be designed carefully at next step.
3. The class of workers and masters should be more brief and commom.

## 