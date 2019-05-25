把该文件夹挂载在放置在上次上传的docker镜像中的即可.
程序逻辑顺序是:
start_main.sh->main.py
start_outloop.sh->LoopTest1.py
start_ncsloop.sh->LoopTest2.py
start_evaluation1.sh->single_threading1.py
start_evaluation2.sh->single_threading2.py
start_evaluation3.sh->single_threading3.py

测试时可以用run_all.sh 并行提交所有的任务.

