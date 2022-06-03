#include <stdio.h>
#include <string.h>
#include <sys/time.h>

#ifndef TOTAL_COUNT
#define TOTAL_COUNT 1000
#endif

int done = 0;

void __attribute__((blocking, yield))yield(){
}


void one(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    i++;
  }
  done++;
}

void two(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    yield();
    i++;
  }
  done++;
}

void three(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    yield();
    yield();
    i++;
  }
  done++;
}

void four(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    yield();
    yield();
    yield();
    i++;
  }
  done++;
}

void five(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    yield();
    yield();
    yield();
    yield();
    i++;
  }
  done++;
}

void six(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    i++;
  }
  done++;
}

void seven(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    i++;
  }
  done++;
}

void eight(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    i++;
  }
  done++;
}

void nine(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    i++;
  }
  done++;
}

void ten(){
  int i = 0;
  while(i<TOTAL_COUNT){
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    yield();
    i++;
  }
  done++;
}
typedef int (*fptr)(void *);
int __attribute__((blockingstack(ten))) context;
fptr list[] = {one, two, three, four, five, six, seven, eight, nine, ten, NULL};
int main(){
  int i;
  printf("Hello\n");
  for(i=0;i<10;i++){
    printf("Item %d\n", i);
    if(list[i]){
//      printf("STarting %d\n", i);
      memset(&context, 0, sizeof(context));
      asm volatile("nop");
      asm volatile("nop");
      asm volatile("nop");
      do{
        if(!(*list[i])(&context)){
//          printf("exitting with done = %d\n", done);
        }else{
//          printf("y");
        }
      }while(done == i);
      asm volatile("nop");
      asm volatile("nop");
      asm volatile("nop");
    }else{
//      printf("wtf\n");
    }
  }
}
