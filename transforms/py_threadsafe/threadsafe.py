#!/usr/bin/python
import xml.dom.minidom

RETURN_VAR = "stack_return"

class visitor:
  def enter(self, node):
    pass
  def leave(self, node):
    pass
  def visit(self, node):
    self.dom = node
    self.visit_r(node)
  def visit_r(self, node, count=0):
    #    print " "*count, node.nodeType, node.nodeName
    self.enter(node)
    #here we check to see if this is a function call...
    for child in node.childNodes:
      if(child.nodeType == child.ELEMENT_NODE):
        self.visit_r(child, count+1)
    self.leave(node)

#searching visitor states

class SearchArgs(visitor):
  IDLE, INFUNCTION, INRESULT, INPARAMS, INVARS, INBODY  = range(6)
  def __init__(self, functions, args, global_lock):
    self.functions = functions
    self.args = args
    self.state = self.IDLE
    self.current = ""
    self.global_lock = global_lock
    self.global_complete = False

  def enter(self, node):
    if(self.state == self.IDLE):
      if(node.nodeName == "functionDefinition"):
        title = node.getAttribute("name")
        if(title in self.functions):
          #Here we do a sanity check to make sure thie isn't a varargs (which wouldn't work)

          self.state = self.INFUNCTION
          self.current = title
          self.isvoid = False
          self.body = None
          #self.current_struct = "stack_struct_" + title
          #self.current_var = "stack_struct_%s_v" % title
          self.newtitle = "thread_safe_%s"%title
          node.setAttribute("name",self.newtitle)
          print "Found function %s" % title
          self.functions.remove(title)
    elif(self.state == self.INFUNCTION):
      if(node.nodeName == "result"):
        if(node.parentNode.getAttribute("isVarArgs") != "false"):
          print "Error, %s has a variable length number of arguments %s, so it cannot be transformed."%(title, node.parentNode.getAttribute("isVarArgs"))
          exit(1)
        print "found a result"
        self.state = self.INRESULT
      elif(node.nodeName == "formalParameters"): 
        print "found params"
        self.state = self.INPARAMS
      elif(node.nodeName == "localVariables"):
        print "found vars"
        self.state = self.INVARS
      elif(node.nodeName == "functionBody"):
        print "found body"
        self.state = self.INBODY
    elif(self.state == self.INBODY):
      pass

    else:
      pass
  def leave(self, node):
    if((self.state == self.INRESULT) and (node.nodeName == "result")):
      self.state = self.INFUNCTION
      print "Leaving a result"
      if(len(node.getElementsByTagName("type"))):
        target = node.getElementsByTagName("type")[0]
        #here we store the return value as an argument
        self.args[self.current] += [("stack_return",target)]
      else:
        self.isfalse = True
    elif((self.state == self.INPARAMS) and (node.nodeName == "formalParameters")):
      print "Leaving params"
      self.state = self.INFUNCTION
      for param in node.getElementsByTagName("parameter"):
        self.args[self.current] += [(param.getAttribute("name"), param.getElementsByTagName("type")[0])]
    elif((self.state == self.INVARS) and (node.nodeName == "localVariables")): 
      print "leaving vars"
      self.state = self.INFUNCTION
    elif(self.state == self.INBODY):
      if(node.nodeName == "functionBody"):
        print "leaving body"
        self.state = self.INFUNCTION

    elif((self.state == self.INFUNCTION) and (node.nodeName == "functionDefinition")):
      print "Leaving function"
      self.state = self.IDLE
      #now create a function that wraps the other one
      newfunc = self.dom.createElement("functionDefinition")
      newfunc.setAttribute("name",self.current)
      newfunc.setAttribute("isInline","false")
      newtype = self.dom.createElement("type")
      newtype.setAttribute("kind","function")
      newtype.setAttribute("isVarArgs","false")
      result = self.dom.createElement("result")
      if(not self.isvoid):
        result.appendChild(self.args[self.current][0][1].cloneNode(True))
      newtype.appendChild(result)
      for arg in self.args[self.current]:
        if(arg[0] != "stack_return"): #we already handled the return value
          obj = self.dom.createElement("parameter")
          obj.appendChild(arg[1].cloneNode(True))
          newtype.appendChild(obj)
      newfunc.appendChild(newtype)

      #Now we re-create formal parameters
      parms = self.dom.createElement("formalParameters")
      for arg in self.args[self.current]:
        if(arg[0] != "stack_return"): #we already handled the return value
          obj = self.dom.createElement("parameter")
          obj.setAttribute("name",arg[0])
          obj.appendChild(arg[1].cloneNode(True))
          parms.appendChild(obj)
      newfunc.appendChild(parms)

      #append local variables and the body
      locals = self.dom.createElement("localVariables")
      if(not self.isvoid):
        local = self.dom.createElement("local")
        local.setAttribute("name", "stack_return")
        local.appendChild(self.args[self.current][0][1].cloneNode(True))
        locals.appendChild(local)
      newfunc.appendChild(locals)


      s = """ {

"""   
      if(not self.global_lock):
        if(not self.global_complete):
          s += "  #include <pthread.h>\n"
          self.global_complete = True
        s += "  static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;\n"
      s += "  pthread_mutex_lock(&mutex);\n"
      if(not self.isvoid):
        s += "  stack_return = "
      s += '  %s('%self.newtitle
      s += ",".join([arg[0] for arg in self.args[self.current][1:]])
      s += "  );\n"
      s += "  pthread_mutex_unlock(&mutex);\n"
      if(not self.isvoid):
        s += "  return stack_return;\n" 
      s += "}\n\n"
      body = self.dom.createElement("functionBody")
      fakebody = self.dom.createElement("pre")
      txt = self.dom.createTextNode(s)
      fakebody.appendChild(txt)
      body.appendChild(fakebody)
      newfunc.appendChild(body)
      #here we find the index of the current node, and place it after it
      idx = node.parentNode.childNodes.index(node)
      node.parentNode.insertBefore(newfunc, node.parentNode.childNodes[idx+1])
      if(self.global_lock):
        if(not self.global_complete):
          pre = self.dom.createElement("pre")
          pre.appendChild(self.dom.createTextNode("#include <pthread.h>\npthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;\n\n"))
          node.parentNode.insertBefore(pre, newfunc)
          self.global_complete = True

def thread_safety(functions, args, input, output, global_threading):
  v = SearchArgs(functions, args, global_threading)
  dom = xml.dom.minidom.parse(input)
  print "Changing stacks..."
  v.visit(dom)
  open(output,"w").write(dom.toxml())

if __name__ == "__main__":

  import sys, os
  global_safety = True
  # Parse a file!
  if len(sys.argv) < 4:
    print 'usage: %s list_of_function_names.txt infile.xml outfile.xml [false for function local safety]'%sys.argv[0]
    sys.exit(1)
  functionlist = sys.argv[1]
  input = sys.argv[2]
  output = sys.argv[3]
  if(len(sys.argv) > 4):
    if(sys.argv[4].lower() == "false"):
      global_safety = False
  if input == output:
    print 'error: in-file and out-file names must be different'
    sys.exit(1)
  if os.path.exists(output):
    print 'error: out-file already exists'
    sys.exit(1)
  if not os.path.exists(functionlist):
    print 'error: list of functions file must exist and be a list of the function names to transform'
    sys.exit(1)
  functions = open(functionlist).read().strip().split('\n')
  args = {}
  for f in functions:
    args[f] = []
  thread_safety(functions, args, input, output, global_safety)

