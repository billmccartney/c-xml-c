#!/usr/bin/python
from subprocess import *
import sys
global_debug = False
def myrun(args):
  """Returns stdout and stderr combined along with an exit code
    (errorcode, stdout)
  """
  if(global_debug):
    print "Running :'%s'" % (" ".join(args))
  p = Popen(" ".join(args), shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
  output = p.stdout.read()
  retval = p.wait()
  if(global_debug):
    print "retval = ", retval

  return retval, output

def parseout(title,s):
  line1 = "Thread Creation Timediff = "
  #line2 = "Running 10000 Threads 100 Iterations Timediff = "
  line2 = "Iterations Timediff = "
  line3 = "Successfully allocated "
  creation = -1
  execution = -1
  threads = -1
  iterations = -1
  size = -1
  if("0xDEADBEEF" in s):
    for line in s.split("\n"):
      if(line1 in line):
        creation = line[len(line1):]
      if(line3 in line):
        size = line[len(line3):]
      if(line2 in line):
        partial = line.split(line2)
        execution = partial[1]
        partial = partial[0].strip().split(" ")
        threads = partial[1]
        iterations = partial[3]
  print "%s,%s,%s,%s,%s,%s"%(title,threads, iterations, size, creation, execution)
def main():
  for threads in [int(10**(i*2)) for i in xrange(1,5)]:
    #Here we compile for each one:
    myrun(["make clean"])
    for prog in ["./app","./appcxmlc"]:
      myrun(["make %s MAXTHREADS=%d ITERATIONS=10"%(prog,threads)])
      for i in xrange(0,10):
        r,o = myrun([prog])
        data = parseout(prog, o)
if __name__ == "__main__":
  main()
