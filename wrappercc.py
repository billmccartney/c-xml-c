#!/usr/bin/python
# This is the gcc wrapper for C-XML-C (www.cxmlc.com)
# See license.txt for license details
# Bill McCartney June 26, 2011

import sys, ConfigParser, os, random, string, shutil
from subprocess import *
import tempfile

#This variable is set to true if this is a unix-like system
IS_UNIX = hasattr(os,"uname")
global_debug = False
force_c = False #This will only copy the output to a c file instead of compiling it.
force_c_filename = ""
class ccpass:
  def __init__(self, command, stdout, debug, reprocess, index):
    self.command = command
    self.stdout = stdout
    self.index = index
    self.debug = debug
    self.reprocess = reprocess
    self.check()
  def check(self):
    if("%1" not in self.command):
      raise Exception("%1 is not included in the command argument of "+self.index)
    if(("%2" not in self.command) and stdout):
      raise Exception("%2 is not included in the command argument of "+self.index)

class config:
  def __init__(self, filename):
    self.config = ConfigParser.RawConfigParser()
    self.config.read(filename)
    self.passes = []
    idx = 1
    section = 'Pass%d'%idx
    while(self.config.has_section(section)):
      self.passes += [ccpass(
        self.myget(section, "command",""), 
        self.myget(section, "stdout",False),
        self.myget(section, "debug",False),
        self.myget(section, "reprocess",False),
        section
        )]
      idx += 1
      section = 'Pass%d'%idx
    self.output = self.myget("Output","command","")
    self.platform = self.myget("Output","platform","native")
    self.path = self.myget("Output","path",os.path.abspath(filename))
    global global_debug
    global_debug = self.myget("Output","debug",False)
    #since we have successfully loaded the config file, add it's path to the system path to possibly find any translations
    newpath = os.path.split(os.path.abspath(filename))[0] #this grabs the absolute folder of the config file
    os.environ["PATH"] += [";",":"][int(IS_UNIX)]
    os.environ["PATH"] += newpath

  def myget(self, section, option, default):
    if(self.config.has_option(section, option)):
      return self.config.get(section, option)
    else:
      return default

def loadconfig():
  #this searches for a global variable first, and then errors out
  #FIXME - add a default search path
  if(os.environ.has_key("CXMLC_CONFIG")):
    return config(os.environ["CXMLC_CONFIG"])
  else:
    try:
      return config("config.ini")
    except:
      raise Exception("Path to config file must be specified via CXMLC_CONFIG")
def myrun(args):
  """Returns stdout and stderr combined along with an exit code
    (errorcode, stdout)
  """
  if(global_debug):
    print "Running :'%s'" % (" ".join(args))
  p = Popen(" ".join(args), shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)#, close_fds=True)
  output = p.stdout.read()
  retval = p.wait()
  if(global_debug):
    print "retval = ", retval

  return retval, output

class Compiler:
  def __init__(self, name):
    self.name = name
  def __str__(self):
    return self.name
  def __repr__(self):
    return "<Compiler: %s>" % self
Compiler.RUNNING = Compiler("Running")
Compiler.FAKE = Compiler("Fake")
Compiler.BYPASS = Compiler("BYPASS")
Compiler.IDLE = Compiler("Idle")

HEADER = "CXMLC"
FILE_SEPERATOR = "$$$$"
SEPERATOR = "####"

class ArgProcessor:
  def __init__(self, args):
    self.args = args
    self.inputs = []
    self.finalargs = []
    self.state = Compiler.RUNNING
    self.output = ""
    self.config = None
    self.processArgs()
    if(not self.config):
      self.config = loadconfig()
    self.compile()
  def processArgs(self):
    i = 1
    while(i<len(self.args)):
      temp = self.handlearg(i, self.args[i])
      i += 1
      if(temp):
        i += 1
  def joinargs(self, newargs):
    for c in newargs:
      if(c not in self.finalargs):
        self.finalargs += [c]
  def preprocess(self, cinputs):
      #FIXME - this is hardcoded with GCC defaults
      result, preprocessor = myrun([self.config.output] + self.finalargs + cinputs + ["-E"])
      if(global_debug):
        print  " ".join([self.config.output] + self.finalargs + cinputs + ["-E"])
      if(result != 0):
        print "Error while preprocessing the files: %s" % preprocessor
        sys.exit(result)
      #Here is an ugly hack to remove license stuff from microchip which looks like
      #Microchip MPLAB C30 License Manager Version v3_24 (Build Date Jul 12 2010).
      #Copyright (c) 2008 Microchip Technology Inc. All rights reserved.
      #The MPLAB C30 license has expired.
      test = "Microchip MPLAB C30 License Manager Version"
      if(preprocessor.startswith(test)):
        vals = ["Options have been disabled due to expired license","Visit http://www.microchip.com/ to purchase a new key.","Microchip MPLAB C30 License Manager Version v3_24 (Build Date Jul 12 2010).","Copyright (c) 2008 Microchip Technology Inc. All rights reserved.","The MPLAB C30 license has expired."]
        for v in vals:
          preprocessor = preprocessor.replace(v,"")
        #idx = 0
        #for i in xrange(0,3):
        #  idx = preprocessor.index("\n",idx+1)
        #preprocessor = preprocessor[idx+1:]
      return preprocessor
  def toxml(self, dummyfilename):
      result, data = myrun([self.cillypath] + dummyfilename + ["--dowritexml"])
      #result, data = myrun([self.cillypath] + dummyfilename + ["--disallowDuplication", "--noLowerConstants", "--decil", "--noInsertImplicitCasts", "--dowritexml"])
      if(result):
        print "Error while c-xml:",data
        sys.exit(result)
      return data
  def runpass(self, cmd, idx):
    code, data = myrun([cmd])
    if(code):
      #here we print the error code that xmlc returned, and exit
      print "Error running pass %d:"%idx, data
      sys.exit(code)
    return data
  def xmltoc(self, xmlfilename):
    xmlcpath = os.path.join(self.config.path,"bin","xmlc.py")
    code, data = myrun([xmlcpath, xmlfilename])
    if(code):
      #here we print the error code that xmlc returned, and exit
      print "Error running xml to c:", data
      sys.exit(code)
    return data
  def writefile(self, filename, data):
    f = open(filename, "w")
    f.write(data)
    f.close()
  def compile(self):
    if(self.state == Compiler.IDLE):
      #WTF do we do here? I guess try to compile to an a.out
      pass
    elif(self.state == Compiler.BYPASS):
      code, output = myrun([self.config.output]+self.args[1:])
      if(code):
        print "Error code:%d" % code
        print output
        sys.exit(code)
    elif(self.state == Compiler.FAKE):
      if(self.output):
        f = open(self.output,"w")
        f.write(HEADER + SEPERATOR.join([FILE_SEPERATOR.join(['"'+os.path.abspath(x)+'"' for x in self.inputs])] + self.finalargs))
        f.close()
      else:
        for c in self.inputs:
          if(c.endswith(".c")):
            f = open(c[:-2]+".o","w")
            f.write(HEADER + SEPERATOR.join(['"'+os.path.abspath(c)+'"']+self.finalargs))
            f.close()
    elif(self.state == Compiler.RUNNING):
      #here we have to go through each of the files being compiled together and try to (naively) merge the files
      cinputs = []
      for c in self.inputs:
        if(c.endswith(".o")): #here we have to check and make sure that we created this .o file
          f = open(c)
          if(f.read(5) == "CXMLC"): #this is a key that starts every cxmlc .o file
            data = f.read().split(SEPERATOR)
            self.joinargs(data[1:])
            self.inputs += data[0].split(FILE_SEPERATOR)
            #cinputs += 
          else:
            raise Exception("%s is an invalid object file created outside of C-XML-C"%c)
          f.close()
        else:
          cinputs += [c]
      if(global_debug):
        print "cfiles: %s args: %s" % (cinputs, self.finalargs)
      #Create a temporary directory
      temp = os.path.abspath(os.path.join(os.curdir,"cxmlc"))#tempfile.mkdtemp()
      shutil.rmtree(temp, True) #remove the folder ignoring any errors
      os.mkdir(temp)
      #print temp
      dummyfilename = os.path.join(temp,"Pass0.c")
      self.writefile(dummyfilename, "") #here we write a dummy file
      #First run the pre processor on each file
      idx = 0
      for f in cinputs:
        if(global_debug):
          print "preprocessing %s" % f
        preprocessor = self.preprocess([f])
        self.writefile(os.path.join(temp, "input%d.c" % idx), preprocessor)
        idx += 1
      self.cillypath = os.path.join(self.config.path,"cil","cilly."+self.config.platform)
      #cinputs += [dummyfilename] #FIXME - I think this is wrong... i think it should be replacing not adding to...
      data = self.toxml([dummyfilename] + [os.path.join(temp,"input%d.c" % idx) for idx in xrange(0,len(cinputs))])
      xmlfilename = "stdo.xml"#dummyfilename[:-2]+".xml"
      #FIXME -- do the passes here...
      #pick a random base name
      if(len(self.output)):
        base = self.output.replace("\\","").replace("/","").replace(".","")
      else:
        base = ''.join(random.sample(string.letters+string.digits, 10))
      idx = 1      
      #This is the main loop for passes...
      for c in self.config.passes:
        newxmlfilename = os.path.join(temp, "Pass%d.xml"%idx)
        if(global_debug):
          print "Pass ",idx
        if(c.reprocess and (idx!=1)): #if we need to reprocess (and it isn't the first pass)
          data = self.xmltoc(xmlfilename)
          tempfilename = os.path.join(temp,"Pass%d.c"%idx)
          self.writefile(tempfilename, data)
          #now re-preprocess this file, and then add support for the other stuff...
          data = self.preprocess([tempfilename])
          tempfilename2 = os.path.join(temp,"PrePass%d.c"%idx)
          self.writefile(tempfilename2, data)
          data = self.toxml([tempfilename2])
          xmlfilename = tempfilename2[:-2]+".xml"
        #replace the %1 and %2 with the input and output filenames respectively
        cmd = c.command.replace("%1",xmlfilename).replace("%2",newxmlfilename)
        if(global_debug):
          print "Running :",cmd
        data = self.runpass(cmd,idx)
        if(c.debug):
          print "output :",data
        xmlfilename = newxmlfilename
        idx += 1
      #nextxmlfilename = xmlfilename
      if(global_debug):
        print "About to xml-c"
      data = self.xmltoc(xmlfilename)
      finalfilename = os.path.join(temp,"final.c")
      f = open(finalfilename, "w")
      f.write(data)
      f.close()
      #Now that we have a c file on the output, we have to finally perform the ACTUAL compilation :)
      outputs = []
      if(self.output):
        outputs = ["-o",self.output]
      code = 0
      if(force_c):
        f = open(force_c_filename, "w")
        f.write(data)
        f.close()
      else:
        code, data = myrun([self.config.output] + self.finalargs + [finalfilename] + outputs) #FIXME - this is gcc specific
        if(global_debug):
          print data
      #help(exit)
      sys.exit(code)
  def handlearg(self, idx, arg):
    if(arg == "-o"):
      #self.state = Compiler.RUNNING
      self.output = self.args[idx+1]
      return 1
    elif(arg in ["-E","-S","-v"]): #These shouldn't get hit, it is when the compiler should output preprocessed output OR assembly code
      #it also passes through for -v argument, which prints out the compiler command line arguments WITH the version
      self.state = Compiler.BYPASS
      self.finalargs += [arg]
    elif(arg == "-c"):
      self.state = Compiler.FAKE
    elif(arg == "--debug"):
      global global_debug
      global_debug = True
    elif(arg.startswith("--force-config=")):
      self.config = config(arg[len("--force-config="):])
    elif(arg.startswith("--force-installation-path=")):
      self.config.path = arg[len("--force-installation-path="):]
    elif(arg.startswith("--force-c=")):
      global force_c, force_c_filename
      force_c = True
      force_c_filename = arg[arg.index("=")+1:]
    elif(arg.startswith("-")):
      self.finalargs += [arg]
    elif(arg.endswith(".nc")):
      self.state = Compiler.BYPASS
      self.finalargs += [arg]
    elif(arg.endswith(".o")):
      self.inputs += [arg]
    elif(arg.endswith(".c")):
      self.inputs += [arg]
    #elif(arg.endswith(".ii")): #fixme - I think there is some extension like this for files that are already preprocessed 
    #  self.inputs += [arg]
    else:
      self.finalargs += [arg]

if __name__ == "__main__":
  ArgProcessor(sys.argv)
