FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y python3.8 python3-pip
COPY . /climate/
RUN pip3 install -r /climate/requirements.txt
WORKDIR /climate/
ENV TZ=Europe/Moscow
ENV DEBIAN_FRONTEND=noninteractive
RUN echo $TZ > /etc/timezone && \
    apt-get install -y tzdata && \
    rm /etc/localtime && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean
ENTRYPOINT ["python3", "main.py"]
