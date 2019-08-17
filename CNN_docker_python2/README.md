# CNN demo on Docker

## requairs:
1. Using the container with id "1688" on IP:10.20.95.219 .`docker exec -it 1688 /bin/bash`
2. go to the working path at `/test/CNN_docker_python2`
3. start the servers in a row with cmds listed below:
    1. `python master.py`
    2. `python loop1.py`
    3. `python loop2.py`
    4. `python evaluator.py`
    5. `python main.py`