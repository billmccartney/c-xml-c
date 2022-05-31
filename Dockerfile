# syntax=docker/dockerfile:1
FROM i686/ubuntu:14.04 
RUN apt update
RUN apt install -y gcc
#RUN apt install -y ocaml
RUN apt install -y make patch autoconf
RUN apt install -y wget
#RUN ln -s /usr/lib/ocaml/libcamlstr.a /usr/lib/ocaml/libstr.a
WORKDIR /app
COPY *.patch *.sh .
# This is from pulling a tag from a specific version https://github.com/ocaml/ocaml/tags
RUN wget https://github.com/ocaml/ocaml/archive/refs/tags/3.09.3.tar.gz
RUN ./compile_ocaml.sh
# This is from pulling a tag from a specific version https://github.com/cil-project/cil/tags
RUN wget https://github.com/cil-project/cil/archive/refs/tags/cil-1.3.6.tar.gz
RUN ./compile.sh
FROM python:3.9-slim
#FROM i386/python:3.9-slim
WORKDIR /app
RUN dpkg --add-architecture i386
RUN apt-get update && apt-get install -y libc6-i386 gcc && rm -rf /var/lib/apt/lists/* && apt-get clean
#RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/* && apt-get clean
RUN mkdir /app/cil
RUN mkdir /app/bin
COPY --from=0 /app/cilly.native /app/cil/cilly.native
COPY *.py config.ini test.c ./
COPY xmlc.py /app/bin/xmlc.py
RUN python wrappercc.py test.c