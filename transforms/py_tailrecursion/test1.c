#include <stdio.h>
#include <string.h>
void factorial_i(double number, double * product){
  if(number <= 1){
    return;
  }else{
    *product *= number;
    factorial_i(number - 1, product);
  }
}
double factorial(double number){
  double result = 1;
  factorial_i(number, &result);
  return result;
}


int main(int argc, char * argv[]){
  int i,max;
  int number;
  if(argc < 3){
    printf("USAGE: %s number_of_factorial iterations\n", argv[0]);
    return 1;
  }
  max = atoi(argv[2]);
  number = atoi(argv[1]);
  printf("fact(%d) = %E\n",number, factorial(number));
  for(i=0;i<max;i++){
    factorial(number);
  }
  return 0;
}
