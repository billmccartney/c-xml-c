#include <unistd.h>
int main(int argc, char * argv[]){
  static char * args[1024];
  int i;
  for(i=1;i<argc;i++){
    args[i-1] = argv[i];
  }
  return execv("/home/bill/bill/src/wrappercc.py", args); 
}
