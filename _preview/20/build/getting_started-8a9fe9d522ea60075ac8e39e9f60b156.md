# Notebook Execution

There are two options to work with this course, via Cloud Hub and locally on your machine.

## Cloud Hub

For this course we will use a jupyterlab instance on a dedicated Cloud Hub. The needed instructions will be added on short notice.

## Locally on your own premises

The easiest is to make use of our pre-built docker image which includes all the needed bits and pieces and is actually also used as base image for the Project Pythia Hub instance.

The only thing you need is a running docker service on your local machine.

Then it's just a one-liner:

```bash
$ docker run -ti --name erad2026 -p 8888:8888 -e LOCAL_USER_ID=$UID ghcr.io/openradar/erad2026:latest /srv/conda/envs/notebook/bin/jupyter lab --ip='*' --port=8888
```
Some of the notebooks are utilizing quite some large cloud data files. So a decent network connection (LAN connection) is preferred to make use of those notebooks. Don't try this at the course as bandwidth will be limited.

If you need a connection to the outside world, you can mount local folders and environment variables into the running container. Please check out the [docker documentation](https://docs.docker.com/guides/use-case/jupyter/) for more details

```bash
$ docker run -ti --name erad2026 -p 8888:8888 -v /host/path/to/your/folder:/home/your/folder -e LOCAL_USER_ID=$UID -e YOUR_ENV_VAR=your_env_var ghcr.io/openradar/erad2026:latest /srv/conda/envs/notebook/bin/jupyter lab --ip='*' --port=8888

```
