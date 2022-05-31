# syntax=docker/dockerfile:1
FROM i686/ubuntu:14.04 
RUN apt update
RUN apt install -y gcc
#RUN apt install -y ocaml
RUN apt install -y make patch autoconf

#RUN ln -s /usr/lib/ocaml/libcamlstr.a /usr/lib/ocaml/libstr.a
WORKDIR /app
COPY *.tar.gz *.patch *.sh .
RUN ./compile_ocaml.sh
RUN ./compile.sh
#RUN tar -xvzf ./3.09.3.tar.gz
#RUN cd ocaml-3.09.3/

#FROM i386/alpine:3.16
#FROM i686/ubuntu:14.04 
FROM  python:3.9-slim
WORKDIR /app
RUN dpkg --add-architecture i386
RUN apt-get update && apt-get install -y libc6-dbg libc6-dbg:i386 lib32stdc++6 gcc && rm -rf /var/lib/apt/lists/*
RUN mkdir /app/cil
RUN mkdir /app/bin
COPY --from=0 /app/cilly.native /app/cil/cilly.native
COPY *.py config.ini test.c ./
COPY xmlc.py /app/bin/xmlc.py
#RUN chmod 755 /app/bin/xmlc.py
RUN python wrappercc.py test.c