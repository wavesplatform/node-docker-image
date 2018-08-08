FROM openjdk:9-jre-slim
ENV WAVES_VERSION="0.13.3"
ENV WAVES_LOG_LEVEL="DEBUG"
ENV WAVES_HEAP_SIZE="2g"

MAINTAINER Inal Kardanov <ikardanov@wavesplatform.com> (@ikardanov)

# Install python
RUN apt-get update -y && apt-get install -y python3 \
    python3-pip \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip


RUN pip3 install requests pyhocon pywaves
RUN apt-get install -y curl

WORKDIR /

RUN mkdir /waves-node
COPY hocon-parser.py /waves-node
COPY entrypoint.sh /waves-node
RUN chmod 777 /waves-node/entrypoint.sh

VOLUME /waves
EXPOSE 6869 6868 6863
ENTRYPOINT ["/waves-node/entrypoint.sh"]