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
  def __init__(self, functions, args):
    self.functions = functions
    self.args = args
    self.state = self.IDLE
    self.current = ""

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
          self.vars = None
          self.current_struct = "stack_struct_" + title
          self.current_var = "stack_struct_%s_v" % title
          self.newtitle = "stack_swapped_%s"%title
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
      if(node.nodeName == "base"):
        if(node.hasAttribute("kind")):
          if(node.getAttribute("kind") == "variable"):
            child = node.getElementsByTagName("variableUse")[0]
            name = child.getAttribute("name")
            if(name in [c[0] for c in self.args[self.current]]):
              print "Found a use of the argument %s" % name
              #change the variable access
              child.setAttribute("name",self.current_var)
              #Here we build up the structure access stuff.
              offset = self.dom.createElement("offset")
              offset.setAttribute("kind","fieldAccess")
              fieldAccess = self.dom.createElement("fieldAccess")
              fieldAccess.setAttribute("name",name)
              fieldAccess.setAttribute("hostCompositeName",self.current_var)
              fieldAccess.setAttribute("isBitField","false")
              offset.appendChild(fieldAccess)
              #node.addChild(offset)
              node.parentNode.appendChild(offset)

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
        node.removeChild(target)
        newtype = self.dom.createElement("type")
        newtype.setAttribute("kind","void")
        node.appendChild(newtype)
      else:
        self.isfalse = True
      #here we also have to remove the arguments from the function prototypes
      params = node.parentNode.getElementsByTagName("parameter")
      for p in params:
        node.parentNode.removeChild(p)
      node.parentNode.appendChild(self.dom.createElement("noParameters"))
    elif((self.state == self.INPARAMS) and (node.nodeName == "formalParameters")):
      print "Leaving params"
      self.state = self.INFUNCTION
      for param in node.getElementsByTagName("parameter"):
        self.args[self.current] += [(param.getAttribute("name"), param.getElementsByTagName("type")[0])]
        node.removeChild(param)
    elif((self.state == self.INVARS) and (node.nodeName == "localVariables")): 
      print "leaving vars"
      self.state = self.INFUNCTION
      #newvars = self.dom.createElement("localVariables")
      #node.parentNode.replaceChild(newvars, node)
      #self.vars = node
    elif(self.state == self.INBODY):
      if(node.nodeName == "functionBody"):
        print "leaving body"
        self.state = self.INFUNCTION
      elif(node.nodeName == "return"):
        if(not self.isvoid):
          retval = node.getElementsByTagName("expression")[0]
          txt = self.dom.createTextNode(self.current_var+".stack_return = %s;\nreturn;\n")
          replacement = self.dom.createElement("pre")
          replacement.appendChild(txt)
          replacement.appendChild(retval)
          node.parentNode.replaceChild(replacement, node)

    elif((self.state == self.INFUNCTION) and (node.nodeName == "functionDefinition")):
      print "Leaving function"
      self.state = self.IDLE
      newstruct = self.dom.createElement("pre")
      txt = self.dom.createTextNode("\nstruct "+self.current_struct+"{\n"+ "  %s\n"*len(self.args[self.current])+"}"+self.current_var+";\n\n")
      newstruct.appendChild(txt)
      for a in self.args[self.current]:
        print "fieldDeclaration " ,a
        field = self.dom.createElement("fieldDeclaration")
        field.setAttribute("name",a[0])
        field.setAttribute("isBitField","false")
        print a[1]
        field.appendChild(a[1].cloneNode(True))
        newstruct.appendChild(field)
        
      #place the new struct before anything else
      node.parentNode.insertBefore(newstruct, node)
      #now create a function that wraps the other one
      newfunc = self.dom.createElement("functionDefinition")
      newfunc.setAttribute("name",self.current)
      newfunc.setAttribute("isInline","false")
      #newfunc.setAttribute(
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
      newfunc.appendChild(locals)


      s = """
  {
  #include <ucontext.h>
  ucontext_t current, child;
  //Setup the new context
  void * malloc(size_t size);
  void * newstack = malloc(SIGSTKSZ);
  getcontext(&child);
  child.uc_stack.ss_sp = newstack;
  child.uc_stack.ss_size = SIGSTKSZ;
  //Here force it to return to the 'caller'
  child.uc_link = &current;
"""
      s += '  makecontext(&child, %s, 0);\n'%self.newtitle
      #Now we setup the arguments
      for arg in self.args[self.current]:
        if(arg[0] != "stack_return"): 
          s += '  %s.%s = %s;\n' % (self.current_var, arg[0], arg[0])
      s += """
  //Swap the context
  swapcontext(&current, &child);
  //we return then we are complete
  free(newstack);
"""
      body = self.dom.createElement("functionBody")
      fakebody = self.dom.createElement("pre")
      if(not self.isvoid):
        s += "  return %s.stack_return;\n" % self.current_var
      s += "  }\n"
      txt = self.dom.createTextNode(s)
      fakebody.appendChild(txt)
      body.appendChild(fakebody)
      newfunc.appendChild(body)
      #here we find the index of the current node, and place it after it
      idx = node.parentNode.childNodes.index(node)
      node.parentNode.insertBefore(newfunc, node.parentNode.childNodes[idx+1])
def change_stacks(functions, args, input, output):
  v = SearchArgs(functions, args)
  dom = xml.dom.minidom.parse(input)
  print "Changing stacks..."
  v.visit(dom)
  open(output,"w").write(dom.toxml())

if __name__ == "__main__":

  import sys, os
  # Parse a file!
  if len(sys.argv) != 4:
    print 'usage: %s list_of_function_names.txt infile.xml outfile.xml'%sys.argv[0]
    sys.exit(1)
  functionlist = sys.argv[1]
  input = sys.argv[2]
  output = sys.argv[3]
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
  #functions = find_recursion(input)
  #change_tail(functions, input, output)
  change_stacks(functions, args, input, output)

