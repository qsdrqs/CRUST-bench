To run the following, please clone [SWE Agent](https://github.com/SWE-agent/SWE-agent.git) and set the file paths in the `pipelined_swe_agent.py`

We have created a custom docker image with rustc and cargo installed and uploaded the same to dockerhub. 

We provide a simple demonstration of the task in `demo`.

We also provide the parameters we used for our experiments in the `config` file. 

Finally we also provide the `problem statements` the represent the task for SWE agent.

In general these scripts will create local git repositories from the projects and then run swe agent, which will then propose patches over the respective git repositories. We set the `apply_local_patch` to `true` to apply the changes locally as well. 