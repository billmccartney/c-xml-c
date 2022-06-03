#include <stdio.h>
#include <string.h>
#include <ucontext.h>
#include <stdlib.h>
/*int add(int a, int b){
  return a+b;
}*/
struct add_struct{
  int retval;
  int a;
  int b;
};

struct add_struct add_data;

static void stack_wrapped_add(){
  add_data.retval = add_data.a+add_data.b;
}

int add(int a, int b){
  ucontext_t current, child;
  //Setup the new context
  void * newstack = malloc(SIGSTKSZ);
  getcontext(&child);
  child.uc_stack.ss_sp = newstack;
  child.uc_stack.ss_size = SIGSTKSZ;
  //Here force it to return to the 'caller'
  child.uc_link = &current;
  makecontext(&child, stack_wrapped_add, 0);
  //Setup the arguments
  add_data.a = a;
  add_data.b = b;
  //Swap the context
  swapcontext(&current, &child);
  //we return then we are complete
  free(newstack);
  //Now return the given return value
  return add_data.retval;
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
  printf("a+b = %d\n", add(a,b));
  return 0;
}
