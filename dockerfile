FROM ubuntu:20.04
RUN apt update
RUN apt install -y python3 python3-pip
COPY . /climate/
RUN pip3 install -r /climate/requirements.txt
WORKDIR /climate/
ENTRYPOINT ["python3", "main.py"]
