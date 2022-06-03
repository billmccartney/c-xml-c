#include <stdio.h>
#include <string.h>
#include <stdlib.h>
int add(int a, int b){
  return a+b;
}

int sub(int a, int b){
  return a-b;
}

int main(int argc, char * argv[]){
  int a,b;
  int result;
  if(argc < 3){
    printf("USAGE: %s arg1 arg2\n", argv[0]);
    return 1;
  }
  a = atoi(argv[1]);
  b = atoi(argv[2]);
  printf("a+b = %d\n", sub(add(a,b),0));
  return 0;
}
