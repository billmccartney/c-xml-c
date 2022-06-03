void b(){
}
void c(){
}
void a(){
  b();
}
void d(){
  a();
  b();
  c();
  d();
}
void main(){
  d();
  a();
}
