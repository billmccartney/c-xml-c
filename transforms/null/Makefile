all: app appcxmlc 
PATH:= ${PATH}:../../bin
CFLAGS = -O3
CC = gcc
CC2 = wrappercc.py
MAXTHREADS = 100
ITERATIONS = 100
CXMLC_CONFIG=./config.ini


app: test1.c
	$(CC) $(CFLAGS) -DFIBER -D MAXTHREADS=$(MAXTHREADS) -D ITERATIONS=$(ITERATIONS) -o $@ $^

appcxmlc: test1.c
	$(CC2) $(CFLAGS)  -D MAXTHREADS=$(MAXTHREADS) -D ITERATIONS=$(ITERATIONS) -o $@ $^

clean:
	rm -f ./app ./appcxmlc ./app.exe ./appcxmlc.exe

