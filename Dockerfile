FROM ubuntu:16.04


RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y python3.6 python3.6-dev python3-pip

RUN ln -sfn /usr/bin/python3.6 /usr/bin/python3 && ln -sfn /usr/bin/python3 /usr/bin/python && \
    ln -sfn /usr/bin/pip3 /usr/bin/pip

COPY requirements.txt /sca_python/requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r ./sca_python/requirements.txt

RUN mkdir -p /root/.aws
COPY scripts/_aws/* /root/.aws/

WORKDIR /sca_python
ADD . /sca_python