#!/usr/local/bin/python
# This is the XML-C generator from the C-XML-C project (see www.cxmlc.com)
# See license.txt for license details
# Bill McCartney June 26, 2011
from xml import sax
mylist = []
unimplemented = []
ignored = ["file","lvalue","functionBody","location","length","singleInitializer","argument","name","noParameters","guard","thenBranch","elseBranch"]
types = {}
def unique(mylist):
  return list(set(mylist))

class SimpleHandler(sax.ContentHandler):
  def __init__(self): #, title, number):
    self.stack = []
    self.current = []
    self.current_stack = []
  def startElement(self, name, attrs):
    global keys
    if(name in list(types.keys())):
      node = types[name](name, attrs)
    else:
      node = element(name, attrs)
    node.pyclass = name
    #  temp = "%s" % name.replace(":","_")
    #  node = eval("wrap%s(name, attrs)"% temp)
    #  node.pyclass = temp
    #  #print "Starting Element %s" % name
    #except:
    #  global mylist
    #  print "ERROR UNLABELED TYPES!!!!! USE EXTRA CODE TO IDENTIFY NEW CLASSES!!!(global mylist) - (%s)" % name
    #  if(name not in mylist):
    #    mylist += [name]
    #  node = element(name, attrs)
    node.mydata = ""
    self.stack.append(node)
    self.current_stack.append(self.current)
    self.current = []
    #print "%s%s" % ("  "*len(self.stack), name)
    #if name == 'Function':
    #  t = attrs.get('name',None)
    #  if("__builtin_" not in t):
    #    print "name>%s" % t
  def characters(self, ch):
    #if(len(ch.strip())):
      #print "chars>'%s'(%d)" % (ch,len(ch))
      node = self.stack.pop()
      ch = ch.replace("\n","\\n").replace("\t","\\t")
      node.mydata += ch
      self.stack.append(node)
  def endElement(self,name):
    node = self.stack.pop()

    node.mychildren = self.current
    if(len(self.stack)): #if we are not done...
      self.current = self.current_stack.pop()
      self.current += [node]
    else:
      #print "Done processing...(%d)" % len(self.current)
      self.top = node
    #print "%s%s" % ("  "*len(self.stack), name)
    #t = self.stack.pop()
    #if(t != name):
    #  print "WTF... stack popping failed??? name = %s stacktop = %s" % (name, t)

gindent = 0
def indent():
  global gindent
  gindent += 1
def dedent():
  global gindent
  gindent -= 1

def newline():
  global gindent
  return ("\n"+("  "*gindent))

class element:
  def __init__(self, name, attr):
    self.__name = name
    self.joinval = " "
    for k in list(attr.keys()):
      self.__dict__[str(k)] = attr[k]
    self.mychildren=[]
  def get_name(self):
    return(self.__name)
  def has_child_type(self, type):
    for c in self.mychildren:
      if(c.get_name() == type):
        return True
    return False
  def printout(self, called = False):
    global unimplemented
    if(not called) and (self.joinval == " "):
      if(self.__name not in unimplemented + ignored + list(types.keys())):
        unimplemented += [self.__name]
    if(hasattr(self, "enclosing")):
      if(self.enclosing):
        return(string.join(["("+c.printout()+")" for c in self.mychildren],self.joinval))
    return(self.joinval.join([c.printout() for c in self.mychildren]))
  def setjoinval(self, val):
    self.joinval = val
  #THE FOLLOWING 2 FUNCTIONS ARE TO SUPPORT BITFIELDS!!!!
  def populatecalltree(self, calltree, parent):
    for c in self.mychildren:
      c.populatecalltree(calltree, parent)
  def getindex(self, name):
    return [c.get_name() for c in self.mychildren].index(name)
  def getindeces(self, name):
    return [i for i in range(0,len(self.mychildren)) if self.mychildren[i].get_name() == name]
  def raw(self):
    return self.mydata.replace("\\n","\n").replace("\\t","\t")

class location(element):
  def printout(self):
#    return ("\n#line %s %s"+newline()) % (self.line, self.file)
    #fixme -- removed actual output to debug...
    return ""

types["location"] = location

class block(element):
  def printout(self):
    res = "{"
    indent()
    res += newline()
    res += " ".join([c.printout() for c in self.mychildren])
    dedent()
    res += newline()+"}" + newline()
    return res
types["block"] = block

class compositeTagDefinition(element):
  def printout(self):
    res = ("%s %s {"%(self.kind, self.name))
    indent()
    res += newline()
    res += (newline().join([c.printout() for c in self.mychildren if c.get_name() != "attribute"])) 
    res += "}"
    res += (newline().join([c.printout() for c in self.mychildren if c.get_name() == "attribute"])) 
    res += ";"
    dedent()
    res += newline()
    return res
types["compositeTagDefinition"] = compositeTagDefinition

class fieldDeclaration(element):
  def printout(self):
    if(self.name == "___missing_field_name"):
      self.name = "" #This fixes the corrections that cil makes
    if(self.isBitField == "true"):
      return self.mychildren[0].printtype(self.name) + " : " + self.mychildren[1].mydata + ";"
    else:
      return self.mychildren[0].printtype(self.name) + ";"
types["fieldDeclaration"] = fieldDeclaration

#class attribute(element):
class attribute(element):
  def printout(self):
    #if(self.name == "volatile"): #FIXME - there is a problem with restrict here,
    #  return " volatile "
    #return "__attribute(("+ self.name+"))"
    #return ""
    return self.printtype("")
  def printtype(self, name):
    if(self.name in ["restrict","artificial"]):
      return name
    if(self.name in ["volatile","const","restrict"]):
      return "%s %s" % (self.name, name)
    #here we have to handle asm carefully
    #here we merge any children
    children = ""
    if(len(self.mychildren)):
      children = "("+",".join([c.printtype("") for c in self.mychildren])+")"
    #this is a patch that fixes the msp430 asm attribute
    if(self.name in ["asm"]):
    	return "__"+ self.name+children+" " + name
      
    return "__attribute__((__"+ self.name+"__"+children+")) " + name
#    return self.printout() + " "+name
types["attribute"] = attribute

class compoundInitializer(element):
  def printout(self):
    mytype = self.getindex("type")
    mytype = self.mychildren[mytype]
    results = []
    #if(mytype.kind == "array"):
      #here we build the results
    for item in self.getindeces("arrayIndex"):
      item = self.mychildren[item]
      idx = (item.getindeces("singleInitializer") + item.getindeces("compoundInitializer"))[0]
      results += [item.mychildren[idx].printout()]
    #elif(mytype.kind in ["struct","union"]):
    for item in self.getindeces("field"):
      item = self.mychildren[item]
      idx = (item.getindeces("singleInitializer") + item.getindeces("compoundInitializer"))[0]
      results += [item.mychildren[idx].printout()]
   # else:
   #   raise Exception("%s is currently not supported\n" % mytype.kind)
    return "{\n"+",".join(results)+"\n}\n"
types["compoundInitializer"] = compoundInitializer

class field(element):
  def printout(self):
    ret = " ."
    for c in self.mychildren:
      if(c.get_name() == "fieldAccess"):
        ret += c.name
      elif(c.get_name() in ["singleInitializer", "compoundInitializer"]):
        ret += " = " + c.printout()
      #FIXME - are there any other types we need to support here?
    return ret
types["field"] = field
 
class enumerationTagDefinition(element):
  def printout(self):
    ret = "enum %s \n{\n%s\n};\n"%(self.name, ",\n".join([c.printout() for c in self.mychildren if c.get_name() == "item"]))
    return ret
types["enumerationTagDefinition"] = enumerationTagDefinition 

class item(element):
  def printout(self):
    return "%s = %s" % (self.mychildren[self.getindex("name")].mydata, self.mychildren[self.getindex("value")].mychildren[0].printout())
types["item"] = item

class functionDefinition(element):
  def printout(self):
    #First check for any storage classes...
    storage= self.getindeces("storageClass")
    modifiers = [self.mychildren[c].printout() for c in storage]
    if(self.isInline == "true"):
      modifiers += ["inline"]
    if(len(modifiers)):
      res = " ".join(modifiers) + " "
    else:
      res = ""
    #Here we have to build up the argument list first...
    paramidx = self.getindex("formalParameters")
    params = self.mychildren[paramidx].printout()
    decl_no_type = self.name + params
    #now find and process the type
    typeidx = self.getindex("type")
    #here we add the ellipses
    if(hasattr(self.mychildren[typeidx],"kind")):
      if(self.mychildren[typeidx].isVarArgs == "true"):
        paren_idx = decl_no_type.rindex(")")
        decl_no_type = decl_no_type[:paren_idx] + ", ..." + decl_no_type[paren_idx:]
    #Here we grab the result tag inside of the type
    res += self.mychildren[typeidx].mychildren[0].mychildren[0].printtype(decl_no_type)
    #Now add the local variables and the body
#    res += newline()
    res += "{"
    indent()
    res += newline()
    localidx = self.getindex("localVariables")
    res += self.mychildren[localidx].printout()
#    res += "{\n"
    bodyidx = self.getindex("functionBody")
    res += self.mychildren[bodyidx].printout()
#    res += "}\n"
    dedent()
    res += newline()+"}" + newline()+ newline()
    return res
types["functionDefinition"] = functionDefinition

class formalParameters(element):
  def printout(self):
    return "("+(", ".join([c.printout() for c in self.mychildren]))+")"
types["formalParameters"] = formalParameters

class mytype(element):
  def printout(self):
    if(self.kind == "named"):
      return self.name
    else:
      return self.printtype("")
      #return self.kind

  def printtype(self, name, bitfield=False, width=0):
    res = ""
    index = 0

    if(bitfield):
      return "BITFIELDS ARE BROKEN"
    if(self.kind == "function"):
#      return "FUNCTION POINTERS ARE BROKEN"
      #print "testing :",self.mychildren[0].mychildren[0].printtype("TESTING")
      if("missingproto" in [self.mychildren[i].name for i in self.getindeces("attribute")]):
        return "" #We return nothing if there was no prototype to begin with...
      args = []
      if(self.isVarArgs == "true"):
        args += ["..."]
      return self.mychildren[0].mychildren[0].printtype("(" + name + ")("+",".join([c.printout() for c in self.mychildren[1:] if c.get_name() != "attribute"]+args)+")")
    if(self.kind == "array"):
      #return "ARRAYS ARE BROKEN"
      initial = ""
      idx = self.getindeces("length")
      if(len(idx)):#there should be only one index, if there are none, then skip it
        initial = self.mychildren[idx[0]].printout() #only use the 1st length (if there are more than one, ignore them)
      return self.mychildren[0].printtype(name+"["+initial+"]")
    #FIXME - attributes are broken...
    if("attribute" in [c.get_name() for c in self.mychildren]):
      attrs = self.getindeces("attribute")
      res = " " + " ".join([self.mychildren[a].printout() for a in attrs])
    if(self.kind == "named"):
      return res + self.name + " " +  name
    elif(self.kind == "pointer"):
      myidx = self.getindex("type")
      attrs = " ".join([self.mychildren[i].printout() for i in self.getindeces("attribute")])
      if(len(attrs)):
        attrs = " " + attrs + " "
      #res += self.mychildren[myidx].printout(attrs + name)

      #try:
      #  res += self.mychildren[1].printout()
      #except:
      #  pass
      if(len(self.mychildren) > 2):
        return "ERROR_CHECK_POINTER_HERE "+name
#        res += 
      return res + attrs +" "+ self.mychildren[myidx].printtype("* " + name + " ") + "  "
    elif(self.kind == "void"):
      return res + self.kind + " " + name
#    elif(["attribute"] == unique([c.get_name() for c in self.mychildren])):
#      #If all of our things are attributes...
#      return res + " ".join([c.name for c in self.mychildren] + [self.kind, name]) 
    elif(self.kind == "enumeration"): #since it is enumeration and not enum, we handle it seperately
      return "%s enum %s %s" % (res, self.name, name)
    elif(self.kind in ["struct","union"]):
      return res +" "+self.kind + " " + self.name + " " + name
    elif(self.kind == "gccBuiltinVAList"):
      return res + " __builtin_va_list " + name
    elif(len(self.mychildren)): #FIXME - is this really needed?
      if(len(self.mychildren) != 1):
#        return "ERROR_CHILD_ARGS_HERE "+name
        return self.kind + " " + (" ".join([c.printtype("") for c in self.mychildren]) + name)
      return self.mychildren[0].printtype(self.kind + " " + name)


    else:
      return " " +self.kind + " " + name 
types["type"] = mytype

class constant(element):
  def printout(self):
    if(self.kind == "string"):
      return '"%s"'%self.mychildren[0].printout()
    elif(self.kind == "int"):
      try:
        return '%s' % self.mychildren[0].printout()
      except:
        return self.mychildren[0].printout()
    elif(self.kind == "double"):
      idx = self.getindeces("textualRepresentation")[0]
      return self.mychildren[idx].printout()
    elif(self.kind == "long"):
      return '%sL'%self.mychildren[0].printout()
    elif(self.kind == "unsigned long"):
      return '%sUL' % self.mychildren[0].printout()
    else:
      #return "ERROR_CONSTANT_%s_is_unsupported"%self.kind
      return self.mychildren[0].printout()
types["constant"] = constant

class textualRepresentation(element):
  def  printout(self):
    return self.mydata
types["textualRepresentation"] = textualRepresentation

class value(element):
  def printout(self):
#    print "self.mydata = '%s'"%self.mydata
    if(len(self.mychildren)):
      return self.mydata + element.printout(self)
    return self.mydata
types["value"] = value

class char(element):
  def printout(self):
    return "'" + self.mydata + "'"
types["char"] = char

class storageClass(element):
  def printout(self):
    if(self.mydata == "default"):
      return ""
    else:
      return self.mydata
types["storageClass"] = storageClass

class variableDefinition(element):
  def printout(self,expression = False):
    res = ""
    for c in self.mychildren:
      name = c.get_name()
      if(name == "type"):
        if(len(res)):
          res += " "
        res += c.printtype(self.name)
      elif(name == "storageClass"):
        res = c.printout() + " " + res
      elif(name in ["singleInitializer", "compoundInitializer"]):
        res += " = " + c.printout()
      elif(name == "location"):
        pass #FIXME - for now ignore location markers inside of the variable decls
      elif(name == "attribute"):
        res += " "+c.printtype("")
      else:
        res += " UNKNOWN_Variable_Definition__%s__"%name
    if(not expression):
      return res + ";"+newline()
    else:
      return res
types["variableDefinition"] = variableDefinition

class variableDeclaration(variableDefinition):
  def printout(self, expression = False):
    #Removed extern to fix a problem with Gcc seeing two externs on a variable 
    #return "extern "+variableDefinition.printout(self)
    return variableDefinition.printout(self)
types["variableDeclaration"] = variableDeclaration


total = []
class expression(element):
  def printout(self):
    binops = {
        "multiplication":"*",
        "division":"/",
        "modulus":"%",
        "arithmeticPlus":"+",
        "arithmeticMinus":"-",
        "subtraction":"-",
        "bitwiseAnd":"&",
        "bitwiseOr":"|",
        "bitwiseXor":"^",
        "shiftLeft":"<<",
        "shiftRight":">>",
        "lessThan":"<",
        "equal":"==",
        "notEqual":"!=",
        "greaterOrEqual":">=",
        "lessOrEqual":"<=",
        "greaterThan":">",
        "logicalAnd":"&&",
        "logicalOr":"||",
        "pointerPlusInteger":"+",
        "pointerMinusInteger":"-",
        "pointerMinusPointer":"-",
        }
    unaryops = {
        "bitwiseNot":"~",
        "logicalNot":"!",
        "negation":"-",
        }
    global total
    kind = self.kind
    if(kind == 'constant'):
      if(len(self.mychildren) != 1):
        return "UNKNOWN, Constant expression should only have one child"
      return self.mychildren[0].printout()
    elif(kind == 'cast'):
      return "((" + self.mychildren[0].printtype("") + ")(" + self.mychildren[1].printout() + "))"
    elif(kind == 'unaryOp'):
      return unaryops[self.operator]+" "+self.mychildren[0].printout()
    elif(kind == 'binaryOp'):
      #return " ".join([self.mychildren[0].printout(), binops[self.operator], self.mychildren[1].printout()])
      #Fixed a bug with order of operations, but i think it is overkill...
      return "((%s) %s (%s))" % (self.mychildren[0].printout(), binops[self.operator], self.mychildren[1].printout())
    elif(kind == 'sizeOf'):
      tmp = self.mychildren[0].printout()
      if(tmp.strip() == "__builtin_va_arg_pack"):
        return " " + tmp + "() "
      return " sizeof(" + self.mychildren[0].printout() + ") "
    elif(kind == 'lvalue'):
      return self.mychildren[0].printout()
    elif(kind == 'addressOf'):
      return "(& " + self.mychildren[0].printout() + " )"
    elif(kind == 'startOfArray'):
      return "(& " + self.mychildren[0].printout() + "[0])"
    else:
      #print "ZZZZZZZZZZZZZZZZZZZZZZZZ" + str([total])
      return "UNKNOWN_EXPRESSION_%s"%kind
    #return element.printout(self)
types ["expression"] = expression

class statement(element):
  def printout(self):
    return element.printout(self) + ";"+newline()
types["statement"] = statement

class offset(element):
  def printout(self):
    if(self.kind == "arrayIndex"):
      res =  "["+self.mychildren[0].printout()+"]"
    elif(self.kind == "fieldAccess"):
      res =  "."+self.mychildren[0].name
    else:
      return "UNKNOWN_offset_kind_%s" % self.kind
    if(len(self.mychildren) > 1):
      res += self.mychildren[1].printout()
    return res
types["offset"] = offset

class variableUse(element):
  def printout(self):
    return self.name
types["variableUse"] = variableUse

class instruction(element):
  def printout(self):
    if(self.kind == "assignment"):
      res = " = ".join([c.printout() for c in self.mychildren[0:2]])+";"+newline()
      if(len(self.mychildren) > 2):
        res += self.mychildren[2].printout()
      return res+";"+newline()
    elif(self.kind == "functionCall"):
      return element.printout(self)+";"+newline()
    elif(self.kind == "gccInlineAssembly"):
      return self.asmprintout()+";"+newline()
    else:
      return "UNKNOWN_instruction_%s" % self.kind
  def asmprintout(self):
    res = ""
    res += "__asm"
    try:
      attributeidx = self.getindex("attribute")
      # + self.mychildren[attributeidx].printout()
      #Let's assume that it's a volatile... - FIXME
      res += " volatile"
    except:
      pass
    res += "("
    templateidx = self.getindex("assemblerTemplates")
    res += self.mychildren[templateidx].printout()
    #Now figure out what to print...
    outputidx = self.getindex("outputOperands")
    output = self.mychildren[outputidx].printout().strip()

    inputidx = self.getindex("inputOperands")
    input = self.mychildren[inputidx].printout().strip()

    clobberidx = self.getindex("clobberedRegisters")
    clobber = self.mychildren[clobberidx].printout().strip()
    #only printout the other arguments if they are used...
    if(clobber or input or output):
      res += " : " + output
      if(input or clobber):
        res += " : " + input
        if(clobber):
          res += " : " + clobber
    res += ")"
    res += ";"  + newline()
    return res

types["instruction"] = instruction

class myreturn(element):
  def printout(self):
    res = "return "
    if(len(self.mychildren) > 1): #Make sure there is more than just a location
      res += self.mychildren[0].printout()
    return res
types["return"] = myreturn

class functionCall(element):
  def printout(self):
    res = self.mychildren[0].printout()+"("
    res += ",".join([c.printout() for c in self.mychildren if c.get_name() == "argument"])
#    if(self.has_child_type("argument")):
#      res += self.mychildren[self.getindex("argument")].printout()
    return res+")"
types["functionCall"] = functionCall

class typeDefinition(element):
  def printout(self):
    res = "typedef "+self.mychildren[0].printtype(self.name) + ";"+newline()
    return res
types["typeDefinition"] = typeDefinition

class functionPrototype(element):
  def printout(self):
    if(self.name == "__builtin_va_arg_pack"):
      return "" #Fixes for __builtin_va_arg_pack -- only in CIL 1.3.7
    #print "/* functionPrototype */"
    storage= self.getindeces("storageClass")
    modifiers = [self.mychildren[c].printout() for c in storage]
    if(self.isInline == "true"):
      modifiers += ["inline"]
    res = " ".join(modifiers) + " "
    #Here we find index of tyhe function type:
    idx = self.getindeces("type")[0]
    temp = self.mychildren[idx].printtype(self.name)
    if(len(temp) == 0):
      #Insert a comment saying the function was not defined...
      return "/*Function %s was not defined*/%s" % (self.name,newline())
    res += temp
    #HEre we check for any attribute modifiers
    attrs = " ".join([self.mychildren[i].printout() for i in self.getindeces("attribute")])

    if(len(attrs)):
      res += " " + attrs
    #res = "/* functionproto */ "  + res
    return res + ";" + newline()
types["functionPrototype"] = functionPrototype

class parameter(variableDefinition):
  def printout(self):
    if(not hasattr(self,"name")):
      self.name = ""
    return variableDefinition.printout(self,True)
  def printtype(self, name):
    #This is not a normal print type, it is used inside of attribute parameters
    if(self.kind == "stringConstant"):
      return '"' + self.mydata + '"'
    elif(self.kind == "integerConstant"):
      return self.mydata
    else:
      return " UNKNOWN_PARAMETER__%s " % self.kind
types["parameter"] = parameter        

class local(parameter):
  def printout(self):
    return parameter.printout(self) + ";" + newline() 
types["local"] = local

class myif(element):
  def printout(self):
    res = "if("+self.mychildren[0].printout()+"){" + newline()
    res += self.mychildren[1].printout()+"}"
    myelse = self.mychildren[2].printout()
    if(len(myelse.strip())):
      res += "else{"+self.mychildren[2].printout()+newline() + "}" + newline()
    else:
      res += newline()
    return res
types["if"] = myif

class caseStatement(element):
  def printout(self):
    res = "case " + self.mychildren[0].printout() + ":" + newline()
    return res
types["caseStatement"] = caseStatement

class defaultCaseStatement(element):
  def printout(self):
    return "default:" + newline()
types["defaultCaseStatement"] = defaultCaseStatement

class mybreak(element):
  def printout(self):
    return "break"
types["break"] = mybreak

class infiniteLoop(element):
  def printout(self):
    res =  "for(;;){"+newline()
    res += element.printout(self)
    res += "}"+newline()
    return res
types["infiniteLoop"] = infiniteLoop

class switch(element):
  def printout(self):
    res = "switch("+ self.mychildren[0].printout() +"){"+newline()
    res += self.mychildren[1].printout() + newline() + "}" + newline()
    return res
types["switch"] = switch

class label(element):
  def printout(self):
    res = self.name+":"+newline()
    return res
types["label"] = label

class statementLabels(element):
  def printout(self):
    return self.mychildren[0].name
types["statementLabels"] = statementLabels

class goto(element):
  def printout(self):
    return "goto "+element.printout(self)
types["goto"] = goto

class template(element):
  def printout(self):
    return '"'+self.mydata+'"'
types["template"] = template

class operand(element):
  def printout(self):
    ret = ""
    if(self.has_child_type("constraintString")):
      ret +='"'+self.mychildren[self.getindex("constraintString")].mydata + '"'
    if(self.has_child_type("outputDestination")):
      ret += '('+ self.mychildren[self.getindex("outputDestination")].printout() + ')'
    if(self.has_child_type("loadedInput")):
      ret += '('+ self.mychildren[self.getindex("loadedInput")].printout() + ')'
    return ret
types["operand"] = operand

class base(element):
  def printout(self):
    if(len(self.mychildren) != 1):
      raise(Exception("Error, a base instance should have only one child"))
    if(self.kind == "variable"):
      return self.mychildren[0].printout()
    if(self.kind == "objectAtEffectiveAddress"):
      return "(*("+self.mychildren[0].printout()+"))"
    print("Error, invalid base type %s" % self.kind)
    raise(Exception("Error, invalid base type %s" % self.kind))
types["base"] = base

class preformatted(element):
  def printout(self):
    #print "Got to preformatted with '%s'" % self.mydata
    if(self.mydata.count("%s") == len(self.mychildren)):
      #for c in self.mychildren:
      #  print c.printout()
      output = self.raw()
      for s in [c.printout() for c in self.mychildren]:
        output = output.replace("%s",s,1)
      return output
    else:
      return self.raw()
types["pre"] = preformatted

def mygen(routine, mystr):
  def newroutine(*args):
    try:
      return routine(*args)
    except:
      return "ERROR_EXCEPTION_OCCURED_IN_%s" % mystr
  return newroutine

#Here we prep all the types...
#for t in types.keys():
#  types[t].printout = mygen(types[t].printout, t)
 

if __name__ == "__main__":

  # Create a parser object
  parser = sax.make_parser()
  
  # Tell it what handler to use
  handler = SimpleHandler()
  parser.setContentHandler( handler )
  
  import sys
  # Parse a file!
  parser.parse(sys.argv[1])
  print("/*printout =*/\n",handler.top.printout())
#  print mylist
  print("/*unimplemented = ",unimplemented)
  print("*/")
