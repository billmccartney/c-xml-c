PATH := ${PATH}:../../bin
all: Program.exe app appcxmlc 
CFLAGS = -O0
CC = gcc
CC2 = wrappercc.py

CXMLC_CONFIG=./config.ini
Program.exe: ./volatileFix/Program.cs
	gmcs -out:$@ $^

app: test1.c
	$(CC) $(CFLAGS) -o $@ $^

appcxmlc: test1.c
	$(CC2) $(CFLAGS) -o $@ $^

clean:
	rm -f ./app ./appcxmlc ./Program.exe ./app.exe ./appcxmlc.exe 
