#include <stdio.h>

void f1(void){
  printf("ft1\n");
}
void f2(void){
  printf("ft2\n");
}
void f3(void){
  printf("ft3\n");
}
void g1(int x){
  printf("g1:%d\n",x);
}
void g2(int x){
  printf("g2:%d\n",x);
}
void g3(int x){
  printf("g3:%d\n",x);
}
typedef void (*func1)(void);
typedef void (*func2)(int);

func1 hide(func1 x){
  return x;
}

func1 list1[10];
int list1count = 0;
func2 list2[10];
int list2count = 0;

void post1(func1 f){
  list1[list1count++] = f;
}
void post2(func2 f){
  list2[list2count++] = f;
}

int main(){
  printf("Hello...\n");
  post1(f1);
  post1(hide(hide(hide(f2))));
  post1(f3);
  post2(g1);
  post2(g2);
  post2(g3);

  while(list1count--){
    (*list1[list1count])();
  }
  while(list2count--){
    (*list2[list2count])(list2count);
  }
  printf("done...\n");
  return 0;
}
