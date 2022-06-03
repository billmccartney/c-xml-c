#!/usr/bin/python
import xml.dom.minidom
#Written by Bill McCartney
# This script builds relationship graphs between all of the variables in a
# program and then analyzes the graph to figure out which indirect call
# can be made from where.
functionargs = []
idnames = {}
relations = []

class visitor:
  def enter(self, node):
    pass
  def leave(self, node):
    pass
  def visit(self, node):
    self.dom = node
    self.visit_r(node)
  def children(self, node):
    return [child for child in node.childNodes if child.nodeType == child.ELEMENT_NODE]
  def visit_r(self, node, count=0):
    #    print " "*count, node.nodeType, node.nodeName
    if(self.enter(node)):
      return #skip the rest if the enter statement already took care of it...
    #here we check to see if this is a function call...
    for child in node.childNodes:
      if(child.nodeType == child.ELEMENT_NODE):
        self.visit_r(child, count+1)
    self.leave(node)

class func:
  def __init__(self, id, dom):
    self.id = id
    self.returns = False
    self.result = []
    self.parms = []
    self.ref = dom # This is the dom object of the fcn definition

#searching visitor states
class SearchRelations(visitor):
  IDLE, INCALL, INARGS, INASSIGNLEFT, INASSIGNRIGHT, INDIRECT, RETURN  = range(7)
  def __init__(self):

    #the following are the outputs
    self.functionargs = [] #(functionid, id, idx) 
    self.ids = {}
    self.relations = []    #(righthand, lefthand)
    self.functionrets = [] #(functionid, retvar)
    self.indirectcalls = [] #(variableid)
    self.indirectrefs = [] #these are the dom objects of the indirect calls
    self.functions = []

    #these are temporary state values
    self.state = [self.IDLE]
    self.current_call = []
    self.current_left = []
    self.current_func = None
    self.current_call_ref = []
    self.argcnt = 0
  def enter(self, node):
    if(not hasattr(node, "hasAttribute")):
      print "node %s does not have hasAttribute" % node
      return
    #if something is an offset, then ignore it (that would be an offset to an array)
    if(node.nodeName == "offset"):
      return True
    if(node.nodeName == "functionDefinition"): 
      self.current_func = func(node.getAttribute("id"), node)
      self.ids[node.getAttribute("id")] = node.getAttribute("name")
      #here we parse out the function arguments
      for parm in node.getElementsByTagName("formalParameters")[0].getElementsByTagName("parameter"):
        self.current_func.parms += [parm.getAttribute("id")]
      child = self.children(node)
      for c in child:  
        self.visit_r(c)
      self.functions += [self.current_func] 
      return True
    if(node.nodeName == "return"):
      #here we found a return statement, push the state and then wait and process the children
      self.state.append(self.RETURN)
      child = self.children(node)
      for c in child:  
        self.visit_r(c)
      self.state.pop() 
    #print "enter called..."
    if(node.hasAttribute("id")):
      #if it has a name, remember it...
      if(node.hasAttribute("name")):
        self.ids[node.getAttribute("id")] = node.getAttribute("name")
      #if it is a function reference (but not in a call) then save it
      if(self.getfunc(node.getAttribute("id"))):
        if(self.state[-1] != self.INCALL):
          self.current_call_ref += [node]
      #now parse it normally, to build the relationships
      if(self.state[-1] == self.INASSIGNLEFT):
        self.current_left += [node.getAttribute("id")]
      elif(self.state[-1] == self.INCALL):
        self.current_call += [node.getAttribute("id")]
        if(len(self.state) > 2):
          if(self.state[-2] == self.INASSIGNRIGHT):
            print "!"*100
            self.functionrets += [(node.getAttribute("id"), self.current_left[-1])]
            print "function return found %s -> %s" % (node.getAttribute("id"), self.current_left[-1])
          elif(self.state[-2] == self.INARGS):
            print "print , found a call in an argument of %s" % [(self.current_call[-2], "c"+self.current_call[-1], self.argcnt)]
            self.functionargs += [(self.current_call[-2], "c"+self.current_call[-1], self.argcnt)]
          elif(self.state[-2] == self.RETURN): #if a call was bad during a return statement, the append the call to the functions return possibilities
            self.current_func.result += ["c"+self.current_call[-1]]
          #FIXME - technically we could be in an assignleft case... but why would that happen...
            
      elif(self.state[-1] == self.INASSIGNRIGHT):
        self.relations += [(node.getAttribute("id"), self.current_left[-1])]
        print "Relation found %s -> %s" % (node.getAttribute("id"), self.current_left[-1])
      elif(self.state[-1] == self.INARGS):
        self.functionargs += [(self.current_call[-1], node.getAttribute("id"), self.argcnt)]
        print "Function arg found %s(%s) = %s" % (self.current_call[-1], self.argcnt, node.getAttribute("id"))
      elif(self.state[-1] == self.INDIRECT):
        self.indirectcalls += [node.getAttribute("id")]
        print "indirect call found %s" % node.getAttribute("id")
      elif(self.state[-1] == self.RETURN):
        self.current_func.result += [node.getAttribute("id")]
    if(self.state[-1] == self.INCALL):
      if(node.nodeName == "base"):
        if(node.getAttribute("kind") == "objectAtEffectiveAddress"):
          self.state.pop()
          self.state.append(self.INDIRECT)
    if(node.nodeName == "instruction"):
      if(node.getAttribute("kind") == "assignment"):
       	#we found an assignment
        child = self.children(node)
        self.state.append(self.INASSIGNLEFT)
        current_stack = len(self.current_left)
        self.visit_r(child[0])
        self.state.pop()
        if(len(self.current_left) != current_stack + 1):
          print "(%s)Error found in an assignment... no variable found in the left hand side... skipping stuff..."% self.current_func.id
          return True
        self.state.append(self.INASSIGNRIGHT)
        self.visit_r(child[1])
        self.state.pop()
        return True
    if(node.nodeName == "functionCall"):
      current_stack = len(self.current_call)
      child = self.children(node)
      self.state.append(self.INCALL)
      self.visit_r(child[0])
      t = self.state.pop()
      if(t == self.INDIRECT):
        #we found an indirect, ignore the arguments for now... FIXME
        self.indirectrefs += [node]
        return True
      if(len(self.current_call) != current_stack + 1):
        print "Error found in an assignment... no variable found in the left hand side... skipping stuff..."
        return True
      temp = self.argcnt
      self.argcnt = 0
      self.state.append(self.INARGS)
      for c in child[1:]:  
        self.visit_r(c)
        self.argcnt+=1
      self.argcnt = temp
      self.state.pop()
      return True
  def resolve(self, id):
    s = ""
    myid = id
    #print "Resolving '%s'"%id
    if(myid[0] == "c"):
      s += "called "
      myid = id[1:]
    s += "%s(%s)"%(self.ids[myid],myid)
    return s
  def getfunc(self, id):
    for f in self.functions:
      if(f.id == id):
        return f
    #print "ERROR, function %s not found..." % id
    return None
  def findall(self, id):
    current = [id]
    size = 0
    while(size != len(current)): #keep looping until we don't find anymore
      size = len(current)
      for i in xrange(0,size):
        item = current[i]
        for rel in self.relations: #Iterate through each relation
          #if a relation points to the same item, then add it to our list of current possible sources
          if(rel[1] == item):
            current += [rel[0]]
      current = list(set(current)) # remove any duplicates
    return current
        
  def preprocess(self):
    #here we add the function arguments to relations
    print "*"*100
    for arg in self.functionargs:
      functionid, id, idx = arg
      f = self.getfunc(functionid)
      if(f):
        if(len(f.parms) < idx):
          print "Not enough paramters to put %d into function %d" % (id, functionid)
        else:
          self.relations += [(id, f.parms[idx])]
          self.relations += [(f.parms[idx], id)]
          #print "Adding relation %s" % [(id, f.parms[idx])]
    #Now process all of the returns into relations
    for ret in self.functionrets:
      functionid, id = ret #so functionid is called and the return value is stored in id...
      f = self.getfunc(functionid)
      if(f):
        #here we have to iterate through all of the possible results and add them as needed
        for possibleresult in f.result:
          #print "possibleresult = '%s'"%possibleresult
          #print "new rule %s" % [(possibleresult, id)]
          self.relations += [(possibleresult, id)]
    #now resolve any calls...
    done = False
    while not done:
      for idx in xrange(0,len(self.relations)):
        rel =self.relations[idx]
        if(rel[0][0] == "c"): #it is a call, we need to resolve it
          print "found a call (%s) now resolving it" % rel
          f = self.getfunc(rel[0][1:])
          if(f):
            #here we have to iterate through all of the possible results and add them as needed
            for possibleresult in f.result:
              self.relations += [(possibleresult, rel[1])]
          break
      else:
        done = True
    #now we need to try to simplify our results
    self.indirects={}
    for c in self.indirectcalls:
      self.indirects[c] = [x for x in self.findall(c) if self.getfunc(x) != None]
      
  def myprint(self):
    print "rules:"
    for rel in self.relations:
      print "%s -> %s" % (self.resolve(rel[0]),self.resolve(rel[1]))
    print "indirections  (%d) " %len(self.indirectcalls)
    for c in self.indirectcalls:
      print "indirect call from %s %s" % (self.ids[c], c)
      for id in self.indirects[c]:
#      for id in self.findall(c):
        f = self.getfunc(id)
        
        if(f):
          print "  Calls %s %s" % (self.ids[f.id], f.id)
        #else:
        #  print "    %s %s" % (self.ids[id], id)


  def ReplaceCalls(self):
    """This function replaces all of the indirect calls with 
       calls into a dispatch table."""
    for i in xrange(0,len(self.indirectcalls)):
      call = self.indirectcalls[i]
      node = self.indirectrefs[i]
      pre = self.dom.createElement("pre")
      name = "dispatch_%s" % call
      dispatch = name + "("
      children = self.children(node)
      dispatch  += ",".join(["(unsigned int)%s"]+["%s"]*(len(children)-1))
      dispatch += ")"
      txt = self.dom.createTextNode(dispatch)
      pre.appendChild(txt)
      for c in children:
        pre.appendChild(c.cloneNode(True))
      node.parentNode.replaceChild(pre, node)
  def AddDispatch(self):
    """This function inserts the dispatch functions prior to any calls"""
    calls = []
    for i in xrange(0, len(self.indirectcalls)):
      calls += self.indirects[self.indirectcalls[i]]
    #grabs the first call as an insertion point
    if(len(calls) == 0):
      return
    insertionnode = self.getfunc(calls[-1]).ref
    #make the list of calls unique
    calls = list(set(calls))
    for i in self.indirectcalls:

      #here we use the other function for types
      mynode = self.getfunc(self.indirects[i][0]).ref.cloneNode(True)
      print " modifying ",mynode.getAttribute("name")
      mynode.setAttribute("name", "dispatch_%s" % i)
      #here we determine if the function has a return value (it changes the dispatch)
      ret = mynode.getElementsByTagName("type")[0].getElementsByTagName("result")[0].getElementsByTagName("type")[0]
      has_ret = (ret.getAttribute("kind") != "void")
      mynode.getElementsByTagName("localVariables")
      parms = []
      first = None
      #now iterate through the list of parameters
      for parm in mynode.getElementsByTagName("formalParameters")[0].getElementsByTagName("parameter"):
        if(not first):
          first = parm
        parms += [parm.getAttribute("name")]
      #build up a dom object for the new first parameter
      pre = self.dom.createElement("pre")
      txt = self.dom.createTextNode("int dispatcher")
      pre.appendChild(txt)
      #insert it before the first parameter, or as the only parameter
      if(first):
        first.parentNode.insertBefore(pre, first)
      else:
        mynode.getElementsByTagName("formalParameters")[0].appendChild(pre)
      pre = None
      #now build the body
      args = ",".join(parms)
      body = """
{
  switch(dispatcher){
"""     
      for id in self.indirects[i]:
        #if it's the last one, make it a default...
        if(id == self.indirects[i][-1]): 
          body+= "default: /* case %d: */" %(1 + calls.index(id))
        else:
          body += "case %d:" % (1 + calls.index(id))
        if(has_ret):
          body += " return "
        body += " %s(%s); break;\n" %(self.ids[id], args)
      body += "  }\n}\n"
      pre = self.dom.createElement("pre")
      pre.appendChild(self.dom.createTextNode(body))
      fbody = mynode.getElementsByTagName("functionBody")[0]
      print "About to replace..."
      fbody.removeChild(fbody.getElementsByTagName("block")[0])
      print "Adding..."
      fbody.appendChild(pre)
      print "Done replacing..."
      #here we insert the new dispatch
      insertionnode.parentNode.insertBefore(mynode, insertionnode)
    self.replaceRefs(calls)  

  def replaceRefs(self, calls):
    for node in self.current_call_ref:
      #we assume it is of the type
      #expression.kind=addressOf(lvalue(base(variableUse)))
      #all of this code is just checking for that EXACT format...
      #and then replacing ALL of it if possible
      id = node.getAttribute("id")
      pre = self.dom.createElement("pre")
      pre.appendChild(self.dom.createTextNode("(void *)%d"%(1+calls.index(id))))
      base = node.parentNode
      if(base.nodeName != "base"):
        print "Weird, not a base where we expect.. this may not work..."
        node.parentNode.replaceChild(pre, node)
      lvalue = base.parentNode
      if(lvalue.nodeName != "lvalue"):
        print "Weird, not an lvalue where we expect.. this may not work..."
        base.parentNode.replaceChild(pre, base)
      expr = lvalue.parentNode
      if(expr.nodeName != "expression"):
        print "Weird, not an expression where we expect.. this may not work..."
        base.parentNode.replaceChild(pre, base)
      if(expr.getAttribute("kind") != "addressOf"):
        print "Weird, not an addressOf expressionthis may not work..."
        base.parentNode.replaceChild(pre, base)
      expr.parentNode.replaceChild(pre, expr)   
def findData(input, output=None):
  v = SearchRelations()
  dom = xml.dom.minidom.parse(input)
  print "about to visit..."

  v.visit(dom)
  v.preprocess()
  v.myprint()
  v.ReplaceCalls()
  v.AddDispatch()
  print "Done..."
  open(output,"w").write(dom.toxml())

if __name__ == "__main__":

  import sys, os
  # Parse a file!
  if len(sys.argv) != 3:
    print 'usage: %s infile.xml outfile.xml'%sys.argv[0]
    sys.exit(1)
  input = sys.argv[1]
  output = sys.argv[2]
  #if input == output:
  #  print 'error: in-file and out-file names must be different'
  #  sys.exit(1)
  #if os.path.exists(output):
  #  print 'error: out-file already exists'
  #  sys.exit(1)
  #if not os.path.exists(functionlist):
  #  print 'error: list of functions file must exist and be a list of the function names to transform'
  #  sys.exit(1)
  findData(input,output)

