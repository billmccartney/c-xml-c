#!/usr/bin/python
import xml.dom.minidom


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

class SearchVisitor(visitor):
  IDLE, INFUNCTION, INBODY, INCALL, INNAME, CHECKING = range(6)#FSM for search
  def __init__(self):
    self.state = self.IDLE #Current state of search
    self.lastworking = []  #Stack of name of searching function (gcc extension)
    self.last = [] #Stack of previous state values
    self.working = "" #name of current function
    self.calls = [] #List of recursive functions
  def enter(self, node):
    self.last.append(self.state) #Allow the state to be restored upon leaving
    #this fixes problems if a child function is defined inside of another (gcc extension)
    self.lastworking.append(self.working) 
    if(self.state == self.IDLE): #looking for a function
      if(node.nodeName == "functionDefinition"):
        self.working = node.getAttribute("name")
        self.state = self.INFUNCTION #Entering a function
    elif(self.state == self.INFUNCTION):
      if(node.nodeName == "result"): #Check for return value
        if(node.getElementsByTagName("type")[0].getAttribute("kind") != "void"):
          self.state = self.IDLE #basically if the function does not return void, then ignore
      if(node.nodeName == "functionCall"):
        self.state = self.INCALL #We found a function call
    elif(self.state == self.INCALL):
      if(node.nodeName == "name"):
        self.state = self.INNAME #We found the name of the called function
    elif(self.state == self.INNAME):
      if(node.nodeName == "variableUse"):
        if(self.working  == node.getAttribute("name")):
          self.calls += [self.working]#Found a recursive function
          self.state = self.CHECKING
    elif(self.state == self.CHECKING): 
      if(node.nodeName == "instruction"): #recursive call is not the last instruction
        print "%s is not proper tail recursion :(" % self.working
        if(self.working in self.calls):
          self.calls.remove(self.working)
  def leave(self, node):
    #restore the last state
    laststate = self.last.pop()
    if(self.state == self.CHECKING):
      if(laststate == self.IDLE):
        self.state = laststate
    self.working = self.lastworking.pop()
#del self.IDLE, self.INFUNCTION, self.INBODY, self.INCALL, self.INNAME, self.CHECKING

def find_recursion(input):
  """This routine detected direct recursion only and returns a list of functions
  that are directly recursive."""
  dom = xml.dom.minidom.parse(input)

  #print "About to run visitor"
  v = SearchVisitor()
  v.visit(dom)
  #print "Visitor complete"
  return v.calls

#Transforming visitor states

class TailVisitor(visitor):
  IDLE, INFUNCTION, INPARAMS, INBODY, INCALL, INNAME, REPLACING = range(7)
  def __init__(self, functions):
    self.argnames = []
    self.argvalues = []
    self.functions = functions[:]
    self.state = self.IDLE
    self.last = []
    self.dom = None
    self.working = ""
  def enter(self, node):
    self.last.append(self.state)
    if(self.state == self.IDLE):
      if(node.nodeName == "functionDefinition"):
        if(node.getAttribute("name") in self.functions):
          self.state = self.INFUNCTION
          self.working = node.getAttribute("name")
          self.argnames = []
          self.argvalues = []
    elif(self.state == self.INFUNCTION):
      if(node.nodeName == "formalParameters"):
        self.state = self.INPARAMS
      if(node.nodeName == "functionBody"):
        #Here we have to add a label...
        txt = self.dom.createTextNode("rec_label:")
        x = self.dom.createElement("pre")
        x.appendChild(txt)
        node.insertBefore(x,node.getElementsByTagName("block")[0])
        self.state = self.INBODY
#        node.childNodes = [x]+node.childNodes[:]
    elif(self.state == self.INPARAMS):
      if(node.nodeName == "parameter"):
        self.argnames.append(node.getAttribute("name"))
    elif(self.state == self.INBODY):
      if(node.nodeName == "instruction"):
        if(node.getAttribute("kind") == "functionCall"):
          self.state = self.INCALL
    elif(self.state == self.INCALL):
      if(node.nodeName == "name"):
        self.state = self.INNAME
    elif(self.state == self.INNAME):
      if(node.nodeName == "variableUse"): 
        if(node.getAttribute("name") == self.working):
          self.state = self.REPLACING  #found the recursive call...
          #this sets up the data for the leaving handler on the overall instruction element
    elif(self.state == self.REPLACING):
      if(node.nodeName == "argument"):
        #There should only be 1 child, so we add that to the value list
        self.argvalues.append(node.getElementsByTagName("expression")[0]) 
  def leave(self, node):
    laststate = self.last.pop()
#    if(self.state == self.CHECKING):
#      if(laststate == self.IDLE):
    #if(self.state == self.INFUNCTION):
    #  if(laststate == self.IDLE):
        #print "Found", self.argnames, self.argvalues
    if(self.state == self.REPLACING):
      if(laststate == self.INBODY):
        #here we do the replacement...
        #First check to make sure we have the same number of arguments in both name and value
        if(len(self.argnames) == len(self.argvalues)):
          #Build up the text elements
          mytext = "".join([x+" = %s;\n" for x in self.argnames])
          mytext += "\n goto rec_label;"
          txt = self.dom.createTextNode(mytext)
          newnode = self.dom.createElement("pre")
          newnode.appendChild(txt)
          for t in self.argvalues:
            newnode.appendChild(t.cloneNode(True))
          #here we replace the current node with the new replacement node
          node.parentNode.replaceChild(newnode, node)
      else:
        laststate = self.state
    self.state = laststate

def change_tail(functions, input, output):
  v = TailVisitor(functions)
  dom = xml.dom.minidom.parse(input)
  print "Changing tail..."
  v.visit(dom)
  open(output,"w").write(dom.toxml())

if __name__ == "__main__":

  import sys, os
  # Parse a file!
  if len(sys.argv) != 3:
    print 'usage: %s infile.xml outfile.xml'%sys.argv[0]
    sys.exit(1)
  input = sys.argv[1]
  output = sys.argv[2]
  if input == output:
    print 'error: in-file and out-file names must be different'
    sys.exit(1)
  if os.path.exists(output):
    print 'error: out-file already exists'
    sys.exit(1)
  functions = find_recursion(input)
  change_tail(functions, input, output)
