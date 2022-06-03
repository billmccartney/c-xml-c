#include <stdio.h>
#include <sys/types.h>
#include <stdlib.h>
#include <unistd.h>

#include <errno.h>
#include <string.h>
#include <netdb.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/time.h>
#define THREADID uint32_t
#define THREAD_STATE_IDLE 0
#define THREAD_STATE_WAITING 1 
#define THREAD_STATE_WRITTEN 2
#ifndef MAXTHREADS
#define MAXTHREADS (2*1024*1024)
#endif
#ifndef ITERATIONS
#define ITERATIONS (2)
#endif
static struct timeval t1,t2,t3;
void printtimediff(struct timeval * t1, struct timeval * t2){
  double d=0;
//  printf("1sec=%d 2sec=%d\n", t1->tv_sec, t2->tv_sec);
  d = (t2->tv_sec-t1->tv_sec);
  d += (t2->tv_usec-t1->tv_usec)/1000000.0;
  printf("Timediff = %e\n", d);
}
//Here we add support for FIBERS...
//#define FIBER
#ifdef FIBER
#include <ucontext.h>
#define FIBER_STACK 1024*4
  ucontext_t globalctx; 
//uint8_t fiberstacks[MAXTHREADS][FIBER_STACK];
uint8_t * fiberstacks;
  uint32_t stackcount = 0;
#endif

typedef struct mbox{
  uint8_t state;
  long int data;
}mbox;

struct threadtab{
  int (*fptr)(void *);
#ifdef FIBER
  ucontext_t ctx; 
#else
  void * arg;
#endif
//  char storage[16];//First byte is state - 0 nothing - 1 waiting for write - 2 already written to...
  mbox storage;
  uint8_t state; //0 means not in running queue - 1 means it is
  struct threadtab * next;
};

struct threadtab * xtab_running=NULL;
struct threadtab * xtab_running_end=NULL;

int xtab_count = 0;
struct threadtab xtab[MAXTHREADS];

void __attribute__((blocking, yield))UnStackYield()
{
  //This function swaps the contexts for both, for the stackless method, it forces 
#ifdef FIBER
  swapcontext(&(xtab_running->ctx), &globalctx);
#endif
}

THREADID get_id(){
  uint32_t val;
//  printf("xtab_running-xtab = 0x%08X\n", xtab_running-xtab);

  val = (xtab_running-&xtab[0]);
  //printf("%d\n",val);
  return val;
}
void UnStackSleep(){
  xtab[get_id()].state=0;
}
void UnStackWakeUp(THREADID id){
  if(xtab[id].state)return;
  //If the queue is empty
  if(!xtab_running_end){
    xtab_running = &xtab[id];
    xtab_running_end = &xtab[id];
  }else{
    xtab_running_end->next = &xtab[id];
    xtab_running_end = &xtab[id];
  }
  xtab_running_end->next=NULL;
  xtab[id].state = 1;
}
void WriteMailBox(THREADID address, uint32_t data){
  if(!xtab[address].state){
    if(xtab[address].storage.state == THREAD_STATE_WAITING)
      UnStackWakeUp(address);
  }
  xtab[address].storage.state = THREAD_STATE_WRITTEN;
  xtab[address].storage.data = data;
  //If the mailbox is already full, then block...
  //if(xtab[address].storage[0]==THREAD_STATE_IDLE){
  /*if(xtab[address].state){
      xtab[address].storage[0] = THREAD_STATE_WRITTEN;
      *((uint32_t *)&(xtab[address].storage[1])) = data;
    }
  }else{*/
}

uint32_t ReadMailBox(){
  //If the mailbox is empty, then block
  //0 nothing - 1 waiting for write - 2 already written to...
  THREADID address;
  address = get_id();
  if(xtab[address].storage.state == THREAD_STATE_IDLE){
    xtab[address].storage.state = THREAD_STATE_WAITING;
    UnStackSleep();
    UnStackYield();
  }
  xtab[address].storage.state = THREAD_STATE_IDLE;
  return (xtab[address].storage.data);
}
#ifdef FIBER
void initctx(ucontext_t *new, void (* fcn)(void *)){
  getcontext(new);
  new->uc_link = 0;
  new->uc_stack.ss_sp = fiberstacks + FIBER_STACK*stackcount++;//malloc( FIBER_STACK );
  new->uc_stack.ss_size = FIBER_STACK;
  new->uc_stack.ss_flags = 0;
  if(new->uc_stack.ss_sp == 0){
    perror("malloc: Could not allocate stack");
    exit(1);
  }
  makecontext(new, fcn, 1, NULL);
} 
#endif
void UnStackSpawn(void (*fcnptr)(void *), void * arg, void * stack){
  //printf("******************************************\n");
  //printf("xtab_count = %d\n", xtab_count);
#ifndef FIBER
  (*(unsigned int *)stack) = 0; //Force state to be 0
#endif
  //printf("stack = 0x%08X\n", stack);
  xtab[xtab_count].fptr = (int (*)(void*))fcnptr;
  //printf("xtab = 0x%08X\n", &(xtab[xtab_count]));
#ifndef FIBER  
  xtab[xtab_count].arg =  stack;
#else
  //printf("about to init ctx\n");
  initctx(&(xtab[xtab_count].ctx), fcnptr);
  //printf("inited ctx\n");
#endif
  UnStackWakeUp(xtab_count);
  xtab_count++;
}

void scheduler(){
  printf("Hello..\n");
  struct threadtab * t;
  uint32_t id;
  for(;xtab_running;){
    //printf("About to run 0x%08X\n", xtab_running);
    t = xtab_running;
    //printf("Getting id\n");
    id=get_id();
    //printf("id = %d\n", id);
    {
    //printf("************** INSIDE THREAD\n");
#ifndef FIBER
    int ret;
    //printf("About to start thread\n");
    ret = t->fptr(t->arg);
    //printf("Thread done...%d\n",ret);
#else

    swapcontext(&globalctx, &(t->ctx));

#endif
    //printf("************** OUTSIDE THREAD\n");
      if(xtab_running == xtab_running_end){ //If we are the last/only thread
        printf("Only one thread...\n");
        xtab_running = NULL;
        xtab_running_end = NULL;
      }else
      //Next item...
      xtab_running = xtab_running->next;
      if(t->state){//Basically we need to reschedule
        printf("Rescheduling... 0x%08X\n", (unsigned int)xtab_running);
        UnStackWakeUp(id);
      }
    }
  }
}

#define STACK(type) int __attribute__((blockingstack(#type)))  

  

#define uint8_t unsigned char
typedef struct smylocaldata{
  uint8_t state;
  void * next;
}mylocaldata;
#define localdata mylocaldata 
//These are the routines we need to implement
/*typedef struct sbasethread{
  localdata local;
  uint8_t * context;
} basethread;

typedef struct smutex{
  uint8_t state;
} mutex;*/

/*void lock_mutex(mutex & m){
  if(m->state){
    //We need to block here...
  */ 




/* APP STARTS HERE */


void peers(void * arg){
  for(;;){
    WriteMailBox((get_id()+1)%MAXTHREADS, ReadMailBox());  
    //printf("peers>%d wrote a message\n", get_id());
  }
}

void unique(void * arg){
  unsigned int data, i;
  printf("unique Starting!!!!!!!!!!!\n");
  WriteMailBox(1, 0xdeadbeef);  
  for(i=0;i<ITERATIONS;i++){
    //printf(">>>>>>>>>>>>>>>>>>>>>>>>>>>Waiting for data... %d\n", i);
    data = ReadMailBox();
    WriteMailBox(1, data);
    //printf("Running unique\n");
  }
  printf("Read 0x%08X\n", data);
  gettimeofday(&t3, NULL);
  printf("Running %d Threads %d Iterations ",MAXTHREADS, ITERATIONS);
  printtimediff(&t2, &t3);
  //sleep(10);
  //for(;;);
  exit(1);
}

STACK(peers) * stacks;//[MAXTHREADS-1];
STACK(unique)ustack;

int main(){
  int i;

  //Here we allocate the ram needed for the contexts and stacks
#ifdef FIBER
#define MYSIZE (MAXTHREADS * FIBER_STACK)
#define DEST   fiberstacks
#else
#define MYSIZE (sizeof(STACK(peers))*(MAXTHREADS))
#define DEST   stacks
#endif
  DEST = malloc(MYSIZE);
  if(!DEST){
    printf("malloc failed...\n");
  }
  memset(DEST, 0, MYSIZE);
  printf("Successfully allocated %d\n",MYSIZE);
  printf("Spawning Unique threads..\n");
  gettimeofday(&t1,0);
  UnStackSpawn(unique, NULL, &ustack);
  printf("Spawning peer threads..\n");
  for(i=1;i<MAXTHREADS;i++)UnStackSpawn(peers, NULL, &(stacks[i-1]));
  printf("got here...\n");
    gettimeofday(&t2,0);
    printf("Thread Creation ");
    printtimediff(&t1, &t2);
  printf("Spawned all threads..\n");
  scheduler();  
}

