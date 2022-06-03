PATH := ${PATH}:../../bin
all: app appcxmlc 
CFLAGS = -O0
CC = gcc
CC2 = wrappercc.py

CXMLC_CONFIG=./config.ini


app: test1.c
	$(CC) $(CFLAGS) -o $@ $^

appcxmlc: test1.c
	$(CC2) $(CFLAGS) -o $@ $^

clean:
	rm -f ./app ./appcxmlc ./app.exe ./appcxmlc.exe

