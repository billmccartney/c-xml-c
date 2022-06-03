#!/usr/bin/python
import xml.dom.minidom
PREFIX = "UnStacked_"
RETURN_VAR = "stack_return"
CONTEXT_NAME = "UnStackedCtx"
RETURN_TYPE = "unsigned char"
PREEMPTION = False
PREEMPTION_VAR = "TinyThreadSchedulerP$preempt_flag"

def mode(mymode):
  global DUFFS_DEVICE, LABEL_POINTERS, STATE_TYPE
  DUFFS_DEVICE = (mymode == "duff")
  LABEL_POINTERS = (mymode == "label")
  #LABEL_POINTERS = False #this uses label pointers to branch instead of a homemade branch table
  #DUFFS_DEVICE = True #This uses duffs device instead of branch tables
  if(LABEL_POINTERS):
    STATE_TYPE = "void * "
  else:
    STATE_TYPE = "unsigned char " #This should be 8 or 16 bit numbers, unless label pointers are used (then it must be a void *)
DEBUG = False
TOS_COUNT = 0
class function:
  def __init__(self, title):
    self.args = {}
    self.argorder = []
    self.locals = {}
    self.children = []
    self.isvarargs = False
    self.retval = None
    self.title = title
    self.isblocking = False
    self.isyield = False
    self.isvoid = False
    self.ispreempt = False
  def addarg(self, name, child):
    self.args[name] = child
    self.argorder += [name]
  def addlocal(self, name, child):
    self.locals[name] = child
  def addchild(self, name):
    if(name not in self.children):
      self.children += [name]
  def struct(self, functions, dom):
    #here we precalculate all of the children that are blocking
    children = [c for c in self.children if functions.has_key(c) and functions[c].isblocking and not functions[c].isyield]
    s = "struct %s%s {\n" %(PREFIX, self.title)
    #E - we should add some overflow check that we don't have more than 255 entry points...
    s += "  %s state;\n"%STATE_TYPE
    if((len(self.args) > 0) or not self.isvoid):
      s += "  union {\n"
      if(len(self.args)):
        s += "    struct {\n"
        s += "      %s;\n"*len(self.args)
        s += "    }args;\n"
      #here we check to see if we have a return value, if not, then ignore it...
      if(not self.isvoid):
        s+="    %s\n"
      s += "  } ops;\n"
    if(len(self.locals)):
      s += "  struct {\n"
      s += "    %s\n"*(len(self.locals))
      s += "  }locals;\n"
    if(len(children)):
      s += "  union {\n"
      s += "".join(["    struct %s%s %s;\n"%(PREFIX,c,c) for c in children])
      s += "  }children;\n"
    s += "};\n\n"
    #here we create pre object for this structure
    pre = dom.createElement("pre")
    txt = dom.createTextNode(s)
    pre.appendChild(txt)
    #here we append the required children so the structure will render correctly
    #arguments
    for arg in self.argorder:
      pre.appendChild(self.args[arg])
    #return value (and type)
    if(not self.isvoid):
      ret = dom.createElement("local")
      ret.setAttribute("name",RETURN_VAR)
      ret.setAttribute("isAddressTaken","false")
      ret.setAttribute("isUsed","true")
      ret.appendChild(self.ret) #append the return type (copied from original)
      pre.appendChild(ret)
    #now the local variables
    for local in self.locals:
      pre.appendChild(self.locals[local])
    return pre
  def __str__(self):
    return "function: %s {\nparams\n%s\n\nargs\n%s\n\nchildren%s\n}\n"%(self.title,self.args, self.locals, "\n\t".join(self.children))

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

class ScanAst(visitor):
  IDLE, INFUNCTION, INRESULT, INPARAMS, INVARS, INBODY, INCALL, INCALLERNAME  = range(8)
  def __init__(self):
    self.functions = {} #Dictionary of functions
    self.state = self.IDLE
    self.current = ""
    self.stack = []

  def enter(self, node):
    self.last = self.state
    if(self.state == self.IDLE):
      if(node.nodeName == "functionDefinition"):
        self.current = node.getAttribute("name")
        self.functions[self.current] = function(self.current)
        self.state = self.INFUNCTION
        self.functions[self.current].isvoid = False
        #print "Found function %s" % self.current
    elif(self.state == self.INFUNCTION):
      if(node.nodeName == "result"):
        if(node.parentNode.getAttribute("isVarArgs") != "false"):
          self.functions[self.current].isvarargs = True
        else:
          self.state = self.INRESULT
        #here we check to see if we have a return value
        self.functions[self.current].isvoid = (node.getElementsByTagName("type")[0].getAttribute("kind") == "void")
        if(not self.functions[self.current].isvoid):#if it's not void, grab the return type
          self.functions[self.current].ret = node.getElementsByTagName("type")[0].cloneNode(True)
      elif(node.nodeName == "formalParameters"): 
        #print "found params"
        self.state = self.INPARAMS
      elif(node.nodeName == "localVariables"):
        #print "found vars"
        self.state = self.INVARS
      elif(node.nodeName == "functionBody"):
        #print "found body"
        self.state = self.INBODY
    elif(self.state == self.INRESULT):
      if(node.nodeName == "attribute"):
        if(node.getAttribute("name") == "blocking"): #we found a blocking routine
          self.functions[self.current].isblocking = True
        if(node.getAttribute("name") == "yield"): #we found a blocking routine
          self.functions[self.current].isyield = True
        if(node.getAttribute("name") == "preempt"): #we found a blocking routine
          self.functions[self.current].ispreempt = True
    elif(self.state == self.INPARAMS):
      if(node.nodeName == "parameter"):
        self.functions[self.current].addarg(node.getAttribute("name"),node.cloneNode(True))
    elif(self.state == self.INVARS):
      #Look for local variables
      if(node.nodeName == "local"):
        #Check for static (global) variables
        #print node.getAttribute("name")
        data = "".join(t.nodeValue for t in node.getElementsByTagName("storageClass")[0].childNodes if t.nodeType == t.TEXT_NODE)
        data=data.strip()
        #print "data = '%s'"%data # node.getElementsByTagName("storageClass")[0].nodeValue

        if(data.strip().lower() != "static"):
          #If it isn't a static variable, add it to the list...
          self.functions[self.current].addlocal(node.getAttribute("name"),node.cloneNode(True))
    elif(self.state == self.INBODY):
      if(node.nodeName == "functionCall"):
        self.state = self.INCALL
    elif(self.state == self.INCALL):
      if(node.nodeName == "name"):
        self.state = self.INCALLERNAME
    elif(self.state == self.INCALLERNAME):
      if(node.nodeName == "variableUse"):
        #print "in functioncall -> name -> variable use"
        #print "%s calls %s" % (self.current, node.getAttribute("name"))
        self.functions[self.current].addchild(node.getAttribute("name"))
    else:
      pass
    self.stack += [self.last]
  def leave(self, node):
    self.state = self.stack.pop()

#In the second pass, I need to do the following:
# 1. Create the structures
# 2. Make the variable accesses use the structures
# 3. Make the argument accesses use the structures
# 4. Change function calls to use structures
# 5. Add a sizeof macro for the structure sizes based upon the blockingsize attribute
# 6. Possibly add a check for hitting 'main' as a blocking routine... should it work? FIXME

def populateTree(functions):
  working = True
  blocking = []
  #First identify all the functions that block naturally
  for f in functions:
    if(functions[f].isblocking):
      blocking += [f]
  #now find all functions that call functions that block
  while working:
    working = False
    for f in functions:
      if(f not in blocking):
        for b in blocking:
          if(b in functions[f].children):
            working = True #keep going until we don't change anything
            functions[f].isblocking = True
            blocking += [f]
            break
  print "blocking = ",blocking
  #for c in blocking:
  #  print functions[c].struct(functions,dom)
  return blocking

class Transformer(visitor):
  IDLE, INFUNCTION, INRESULT, INPARAMS, INVARS, INBODY, INCALL, INCALLERNAME  = range(8)
  def __init__(self, functions, blocking):
    self.functions = functions
    self.blocking = blocking
    self.state = self.IDLE
    self.current = ""
    self.mustswap = False
    self.swapname = ""
    self.stack = []
    self.structs_printed = False
  def structs(self):
    #This routine inserts all of the struct types prior to a given node
    blocking = self.blocking[:]
    output = []
    #First we have to find the correct order to call them - FIXME - we only need to do this for the non-recursive method
    while len(blocking):
      for c in blocking:
        for j in self.functions[c].children:
          if(j in blocking):
            break
        else:
          output += [c]
          blocking.remove(c)
          break
    #now that we know the order, let's return a list of the structure objects
    retval = [self.functions[c].struct(self.functions, self.dom) for c in output]
    #if(PREEMPTION):
    #  #here we add a default variable that allows preemption to take place
    #  pre = self.dom.createElement("pre")
    #  pre.appendChild(self.dom.createTextNode("//Preemption Variable\nint %sPreempt = 0;\n" % PREFIX))
    #  retval = [pre] + retval
    return retval
  def getstate(self):
    self.idx += 1
    return str(self.idx)
  def buildjump(self):
    if(LABEL_POINTERS):
      return "if("+CONTEXT_NAME+"->state)goto *("+CONTEXT_NAME+"->state);\n"
    if DEBUG:
      s = 'printf("got into '+self.current+' at state %d\\\\n",'+CONTEXT_NAME+'->state);\n'
    else:
      s = ""
    if(not (LABEL_POINTERS or DUFFS_DEVICE)):
      for i in xrange(1, self.idx+1):
        s += "if(%s->state == %s)goto %s_%s_%s;\n"%(CONTEXT_NAME, i, PREFIX, self.current, i)
    return s
  def makelabel(self):
    #This routine makes the label and returns the label and the code that sets the state
    #it returns a pair of values, namely label, state_routine
    state = self.getstate()
    label = "%s_%s_%s" % (PREFIX, self.current, state)
    if(LABEL_POINTERS):
      s = CONTEXT_NAME + "->state = &&"+label+";\n"
    else:
      s = "%s->state = %s;\n"%(CONTEXT_NAME, state)
    if(DUFFS_DEVICE):
      label = "case " + str(state) +":\n{}\n"
    else:
      label = label +":\n{}\n"
    return label, s
  def enter(self, node):
    self.last = self.state
    if(self.state == self.IDLE):
      #Check to see if we need to print the structures
      if(node.nodeName in ["functionDefinition","variableDefinition","functionPrototype"]):
        if(not self.structs_printed):
          for c in self.structs():
            node.parentNode.insertBefore(c, node)
          self.structs_printed = True
      if(node.nodeName == "functionDefinition"):
        self.current = node.getAttribute("name")
        if(self.current in self.blocking):
          self.state = self.INFUNCTION
          self.idx = 0
        #print "Found function %s" % self.current
    elif(self.state == self.INFUNCTION):
      if(node.nodeName == "result"):
        if(node.parentNode.getAttribute("isVarArgs") != "false"):
          raise Exception("var args are currently not supported... %s" % self.current)
        else:
          self.state = self.INRESULT
      elif(node.nodeName == "formalParameters"): 
        #print "found params"
        self.state = self.INPARAMS
      elif(node.nodeName == "localVariables"):
        #print "found vars"
        self.state = self.INVARS
      elif(node.nodeName == "functionBody"):
        #print "found body"
        self.state = self.INBODY
    elif(self.state == self.INBODY):
      if(self.current in self.blocking):
        if(node.nodeName == "functionCall"):
          self.state = self.INCALL
          self.mustswap = False
    elif(self.state == self.INCALL):
      if(node.nodeName == "name"):
        self.state = self.INCALLERNAME
    elif(self.state == self.INCALLERNAME):
      if(node.nodeName == "variableUse"):
        if(node.getAttribute("name") in self.blocking):
          print "must swap %s in %s" % (node.getAttribute("name"), self.current)
          self.mustswap = True
          self.swapname = node.getAttribute("name")
    #this part of the routine changes any variable accesses to use the structure
    if(self.state in [self.INCALL, self.INBODY]):  
      if(self.current in self.blocking):
        if(node.nodeName == "variableUse"):
          if(node.getAttribute("isGlobal").lower() == "false"):
            #figure out if it is an arg or a automatic var
            name = node.getAttribute("name")
            if(name in self.functions[self.current].locals.keys()):
              #handle it as a key...
              pre = self.dom.createElement("pre")
              txt = self.dom.createTextNode(CONTEXT_NAME +"->locals."+ name)
              pre.appendChild(txt)
              node.parentNode.replaceChild(pre, node)
            elif(name in self.functions[self.current].args.keys()):
              pre = self.dom.createElement("pre")
              txt = self.dom.createTextNode(CONTEXT_NAME +"->ops.args."+ name)
              pre.appendChild(txt)
              node.parentNode.replaceChild(pre, node)
        #print "in functioncall -> name -> variable use"
    #    print "%s calls %s" % (self.current, node.getAttribute("name"))
    #    self.functions[self.current].addchild(node.getAttribute("name"))
    else:
      pass
    self.stack += [self.last]

  def buildProto(self, name):
    return "unsigned char "+name+"(struct "+PREFIX+name+" * "+CONTEXT_NAME + ")"

  def leave(self, node):
    if(self.state == self.INFUNCTION):
      if(node.nodeName == "functionDefinition"):
        #here we replace the function with a pre statement including the new arguments
        pre = self.dom.createElement("pre")
        if(DUFFS_DEVICE):
          txt = self.dom.createTextNode(self.buildProto(self.current)+"{\nswitch("+CONTEXT_NAME+"->state){default:\n%s\n}\nreturn 0;\n}\n")
        else:
          txt = self.dom.createTextNode(self.buildProto(self.current)+"{\n"+self.buildjump()+"{\n%s\n}\nreturn 0;\n}\n")
        pre.appendChild(txt)
        pre.appendChild(node.getElementsByTagName("functionBody")[0].cloneNode(True))

        node.parentNode.replaceChild(pre, node)
    elif(self.state == self.INBODY):
      if(node.nodeName == "return"):
        isvoid = self.functions[self.current].isvoid
        if(isvoid):
          s = "{//Return statement\nreturn 0;\n}"
        else:
          s = "{//Return statement\n"+CONTEXT_NAME+"->ops."+RETURN_VAR+" = %s;\nreturn 0;\n}"
        txt = self.dom.createTextNode(s)
        pre = self.dom.createElement("pre")
        pre.appendChild(txt)
        if(not isvoid):
          pre.appendChild(node.getElementsByTagName("expression")[0].cloneNode(True))
        node.parentNode.replaceChild(pre, node)
      #here we add preemption if needed
      if(node.nodeName == "infiniteLoop"):
        if(PREEMPTION):
          pre = self.dom.createElement("pre")
          label, set = self.makelabel()
          s = "\n{//Preemption\n"
          s += set
          s += "\nif(%s)return 1;\n" % PREEMPTION_VAR
          s += label
          s += "\n}\n"
          pre.appendChild(self.dom.createTextNode(s))
          node.appendChild(pre)


    elif(self.state == self.INCALL):
      if(node.nodeName == "functionCall"):
        if(self.mustswap):
          pre = self.dom.createElement("pre")
          #check to see if the function requires a yield
          if(self.functions[self.swapname].isyield):
            label, set = self.makelabel()
            txt = self.dom.createTextNode("{\n%sreturn 1;%s\n}\n"%(set, label))
            pre.appendChild(txt)
            node.parentNode.replaceChild(pre, node)
          else:
            #Here we setup the alternate calling method:
            print "Setting up %s in %s" % (self.swapname, self.current)
            s = "{//Beginning of function call -- First setup arguments\n"
            for arg in self.functions[self.swapname].argorder:
              s += CONTEXT_NAME + "->children."+self.swapname+".ops.args."+arg+" = %s;\n"
            s += "//Now setup the call\n"
            s += "%s->children.%s.state = 0;\n" % (CONTEXT_NAME, self.swapname)
            label, set = self.makelabel()
            s += "%s\n%s\n" % (set,label)
            s += "if(%s(&(%s->children.%s)))return 1;\n//End of function call\n}\n" %(self.swapname, CONTEXT_NAME, self.swapname)
            #if we are not void put the return value there...

            txt = self.dom.createTextNode(s)
            pre.appendChild(txt)
            for n in node.getElementsByTagName("argument"):
              pre.appendChild(n.cloneNode(True))

            #Now replace the node with the new pre statement
            
            kind = node.parentNode.getAttribute("kind")
            #here we have to check to see what the parent instruction is.
            #If it is a funciton call instruction, then replace the existing call with it
            if(kind == "functionCall"):
              node.parentNode.replaceChild(pre, node)
              print "Replacing a function call.."
            elif(kind == "assignment"):
              if(self.functions[self.swapname].isvoid):
                raise Exception("The function %s is used in an assignment operation, and it is a void function."%self.swapname)
              #create the return placement
              newpre = self.dom.createElement("pre")
              txt2 = self.dom.createTextNode("%s->children.%s.ops.%s;\n"%(CONTEXT_NAME, self.swapname, RETURN_VAR))
              newpre.appendChild(txt2)
              #now put in the funciton call prior to the assignment instruction
              node.parentNode.parentNode.insertBefore(pre, node.parentNode)
              node.parentNode.replaceChild(newpre, node)
            else:
              raise Exception("The function %s called inside of %s is called from something other than an assignment or functionCall instruction."%(self.swapname, self.current))
    if(node.nodeName == "attribute"):
      if(node.getAttribute("name") == "blockingstack"):
        print "Found a blocking stack..."
        #here we do a sanity check and make sure that the parent is a type
        if(node.parentNode.nodeName != "type"):
          raise Exception("The blockingstack attribute should only be used on variable types.")
        newparent = node.parentNode.cloneNode(True)
        newparent.setAttribute("kind","struct")
        #print "should be struct...",node.parentNode.getAttribute("kind")
        name = "".join([c.nodeValue for c in node.getElementsByTagName("parameter")[0].childNodes if c.nodeType == c.TEXT_NODE])
        #This is a hack to support tinyos -- it relies on the module being named TinyThreadPtr.run_thread and that they are in order (0,1,2,etc).
        if(name == "run_thread"):#not in self.functions):
          global TOS_COUNT
          newparent.setAttribute("name",PREFIX + "TinyThreadPtr$" + str(TOS_COUNT) + "$run_thread")
          TOS_COUNT += 1
        else:
          #Here we try to find what function is being talked about...
          if(name not in self.blocking):
            for possiblename in self.blocking:
              if(str(possiblename).endswith(str(name))):#name == ("$".split(possiblename))[-1]):
                newparent.setAttribute("name", PREFIX+possiblename)
                break
            else:
              print "Error, no function named '%s' was found" % (name)
              sys.exit(-1)
          else:
            newparent.setAttribute("name", PREFIX+name)

          
        node.parentNode.parentNode.replaceChild(newparent, node.parentNode)
        for c in newparent.getElementsByTagName("attribute"):
          if(c.getAttribute("name") == "blockingstack"):
            newparent.removeChild(c)
    elif(node.nodeName == "functionPrototype"):
      if(node.getAttribute("name") in self.blocking):
        #Here we have to replace the prototype with an equivalent prototype of the new function
        pre = self.dom.createElement("pre")
        pre.appendChild(self.dom.createTextNode(self.buildProto(node.getAttribute("name"))+";\n"))
        node.parentNode.replaceChild(pre, node)
         
    self.state = self.stack.pop()

def make_stackless(input, output):
  v = ScanAst()
  dom = xml.dom.minidom.parse(input)
  v.visit(dom)
  blocking = populateTree(v.functions)
  t = Transformer(v.functions, blocking)
  t.visit(dom)
  #Now we can reprocess the AST with a second visitor that will actually perform the transform
  #print " ".join([str(v.functions[x]) for x in v.functions])
  open(output,"w").write(dom.toxml())

if __name__ == "__main__":
  import sys, os
  # Parse a file!
  args = sys.argv
  if("-preemption" in args):
    args.remove("-preemption")
    PREEMPTION = True
  if("-preemptionvar" in args[:-1]):
    idx = args.index("-preemptionvar")
    PREEMPTION_VAR = args[idx+1]
    args.remove("-preemptionvar")
    args.remove(PREEMPTION_VAR)
  if len(args) not in [3,4]:
    print 'usage: %s [-preemption] [-preemptionvar %s] infile.xml outfile.xml' % (sys.argv[0], PREEMPTION_VAR)
    sys.exit(1)
  input = args[1]
  output = args[2]
  if(len(args) > 3):
    mode(args[3])
  else:
    mode("generated")
  if input == output:
    print 'error: in-file and out-file names must be different'
    sys.exit(1)
  if os.path.exists(output):
    print 'error: out-file already exists'
    sys.exit(1)
  make_stackless(input, output)

