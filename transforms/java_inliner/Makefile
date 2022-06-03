all: java_inline.class app appcxmlc 
CFLAGS = -O0
CC = gcc
CC2 = wrappercc.py

CXMLC_CONFIG=./config.ini
java_inline.class: java_inline.java xml_visitor.java visitor.java
	javac $^ 

app: test1.c
	$(CC) $(CFLAGS) -o $@ $^

appcxmlc: test1.c
	$(CC2) $(CFLAGS) -o $@ $^

clean:
	rm -f ./app ./appcxmlc ./app.exe ./appcxmlc.exe ./java_inline.class ./xml_visitor.class

