FROM python:3.10-slim-bullseye

ENV TDIR /home/app

RUN mkdir -p $TDIR
COPY ./requirements.txt $TDIR/
COPY ./expose $TDIR/expose
COPY ./extract_stream_load $TDIR/extract_stream_load
COPY ./transform $TDIR/transform
RUN cd $TDIR/ && pip install -r requirements.txt
COPY ./.dbt /root/.dbt
RUN apt-get update && apt-get install -y vim && apt-get install -y git 

CMD /bin/bash