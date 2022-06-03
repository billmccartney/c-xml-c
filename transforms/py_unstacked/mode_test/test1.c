#include <stdio.h>
#include <string.h>
#include <sys/time.h>

#ifndef TOTAL_COUNT
#define TOTAL_COUNT 100000000
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

/* Return 1 if the difference is negative, otherwise 0.  */
int timeval_subtract(struct timeval *result, struct timeval *t2, struct timeval *t1)
{
    long int diff = (t2->tv_usec + 1000000 * t2->tv_sec) - (t1->tv_usec + 1000000 * t1->tv_sec);
    result->tv_sec = diff / 1000000;
    result->tv_usec = diff % 1000000;

    return (diff<0);
}

void timeval_print(struct timeval *tv)
{
    char buffer[30];
    time_t curtime;

    printf("%ld.%08ld", tv->tv_sec, tv->tv_usec);
    curtime = tv->tv_sec;
    strftime(buffer, 30, "%m-%d-%Y  %T", localtime(&curtime));
    printf(" = %s.%08ld\n", buffer, tv->tv_usec);
}


typedef int (*fptr)(void *);
int __attribute__((blockingstack(ten))) context;
fptr list[] = {one, two, three, four, five, six, seven, eight, nine, ten, NULL};
struct timeval tvBegin, tvEnd, tvDiff;
int main(){
  int i;
  for(i=0;i<10;i++){
    if(list[i]){
//      printf("STarting %d\n", i);
      memset(&context, 0, sizeof(context));
      gettimeofday(&tvBegin, NULL);
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
      gettimeofday(&tvEnd, NULL);
      asm volatile("nop");
      asm volatile("nop");
      asm volatile("nop");
      timeval_subtract(&tvDiff, &tvEnd, &tvBegin);
      long long int value = tvDiff.tv_sec * 1000000ll + tvDiff.tv_usec;
//      printf("%ld.%06ld\n", tvDiff.tv_sec, tvDiff.tv_usec);
      printf("(yield = %d) Diff in usec %lld\n", (1+i), value/(1+i));

    }else{
//      printf("wtf\n");
    }
  }
}
