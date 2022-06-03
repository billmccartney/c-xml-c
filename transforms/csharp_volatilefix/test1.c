#include <stdio.h>
#include <string.h>
#include <stdlib.h>
int shared=0;
void interrupt(){
  shared =0 ;
}

int main(int argc, char * argv[]){
  shared = 1;
  printf("Shared = %d\n", shared);
  return 0;
}
