import java.io.File;
//These are for xml parsing/manipulation
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NamedNodeMap;
import org.w3c.dom.NodeList;
import org.w3c.dom.Attr;

//These are used for xml writing
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;

import java.util.*;
import java.io.*;

public class xml_visitor extends visitor{
	 
	List<Element> functions = new ArrayList<Element>();
	List<String> names = new ArrayList<String>();
	List<Element> returns = new ArrayList<Element>();
	List<Boolean> isvoid = new ArrayList<Boolean>();
	String infile, outfile;
	Document dom;
	public xml_visitor(String input, String output){
		infile = input;
		outfile = output;
	}
	private enum state { IDLE, ININLINED, INFUNCTION, ININSTRUCTION, INCALL, INNAME, VALIDCALL}
	private state fsm = state.IDLE;
	int argidx;
	int usagecount = 0;
	String childname;
	public void enter(Element node){
		String name = node.getNodeName();
		System.out.println("ENTER   " + name + ":"+ fsm);
		switch(fsm){
		case IDLE:
			if(name == "functionDefinition"){
				if(node.getAttribute("isInline").toLowerCase().equals("true")){
					//Here we add this function to our list of inlines
					System.out.println(node.getAttribute("name"));
					functions.add(node);
					names.add(node.getAttribute("name"));
					fsm = state.ININLINED;
				}else{
					fsm = state.INFUNCTION;
					//System.out.println(node.getAttribute("name"));
				}
			}
			break;
		case INFUNCTION:
			if(name == "instruction"){
				fsm = state.ININSTRUCTION;
			}
			break;
		case ININSTRUCTION:
			if(name == "functionCall"){
					fsm = state.INCALL;
					argidx = 0;
			}
			break;
		case INCALL:
			if(name == "name"){
				fsm = state.INNAME;
			}
		case INNAME:
			if(name == "variableUse"){
				childname = node.getAttribute("name");
				if(names.contains(childname)){
					System.out.println("Calling "+childname);
					fsm = state.VALIDCALL;
				}else{
					fsm = state.INFUNCTION;
				}
			}
			break;
		case VALIDCALL:
			break;
		case ININLINED:
			if(name == "variableUse"){
				//Here we change the arguments and local variable names prior to inlining to reduce variable collisions 
				if(node.getAttribute("isGlobal").equals("false")){
					node.setAttribute("name", "inlined_"+node.getAttribute("name"));
				}
			}else if(name == "local"){
				//Here we change the local variable names prior to inlining to reduce variable collisions
				node.setAttribute("name", "inlined_"+node.getAttribute("name"));
			}else if(name == "parameter"){
				//Here we change the parameter names prior to inlining to reduce variable collisions
				node.setAttribute("name", "inlined_"+node.getAttribute("name"));
			}else if(name == "result"){
				//Here we create the local variable which returns the value (if needed)
				Element type = (Element)node.getElementsByTagName("type").item(0);
				Boolean isvoidfunc =type.getAttribute("kind").equals("void"); 
				isvoid.add(isvoidfunc);
				if(isvoidfunc){
					returns.add(null);
				}else{
					returns.add((Element)type.cloneNode(true));
				}
			}
			break;
		}
	}

	public void leave(Element node){
		String name = node.getNodeName();
		System.out.println("LEAVE   " + name + ":"+ fsm);
		switch(fsm){
			case ININLINED:
				if(name == "functionDefinition"){
					//Remove the previous function, since it will have no bearing on the output
					node.getParentNode().removeChild(node);
					fsm = state.IDLE;
					//it won't get gc'ed yet since it is still referenced in the list of inline functions
				}
			break;
			case INFUNCTION:
				if(name == "functionDefinition"){
					fsm = state.IDLE;
				}
				break;
			case ININSTRUCTION:
				if(name == "instruction"){
					fsm = state.INFUNCTION;
				}
			break;
			case VALIDCALL:
				if(name == "functionCall"){
					System.out.println(node.getAttribute("GOT TO THE COOL POINT!!"));
					//FIXME, here we replace the function call with an inlined version
					//First find the index of the node in the lists:
					int idx = names.indexOf(childname);
					usagecount++;
					String retname = "inlined_retval" + usagecount;
					String retlabel = "inlined_return" + usagecount;
					Element newchild = functions.get(idx);
					Element pre = dom.createElement("pre");
					String body = "(\n//Inlining "+names.get(idx) + " here\n{%s\n{%s{\n";
					NodeList args = node.getElementsByTagName("argument");
					Element params = (Element) newchild.getElementsByTagName("formalParameters").item(0);
					for (int i = 0; i < args.getLength(); i++) {
						body += ((Element) (params.getElementsByTagName("parameter").item(i))).getAttribute("name") + " = %s;\n";
						//((Element) ).getElementsByTagName("parameter").item(i);
					}
					body += "%s\n}\n}\n";
					body += retlabel+":";
					if(!isvoid.get(idx)){
						body += retname+";";
					}
					body += "\n//End of "+names.get(idx) + " here\n})";
					pre.appendChild(dom.createTextNode(body));
					//Setup the locals
					Element locals = (Element)functions.get(idx).getElementsByTagName("localVariables").item(0).cloneNode(true);
					//If needed add the return value to it...
					if(!isvoid.get(idx)){
						Element retvar = dom.createElement("local");
						
						retvar.setAttribute("name", retname);
						retvar.setAttribute("isAddressTaken","false");
						retvar.setAttribute("isUsed","true");
						
						retvar.appendChild(returns.get(idx).cloneNode(true));
						locals.appendChild(retvar);
					}
					
					pre.appendChild(locals);
					
					//Setup the arguments (which will look like more variables
					Element newparams = (Element)params.cloneNode(true);
					
					//This converts the parameters into a second set of local variables
					pre.appendChild(newparams);
					
					NodeList oldparams = newparams.getElementsByTagName("parameter");
					System.out.println("params " + params.getNodeName());
					
					for (int i = oldparams.getLength()-1; i >= 0 ; i--) {
						System.out.println("Changing argument..*************************");
						rename((Element)oldparams.item(i),"local");
					}
					rename(newparams, "localVariables");
					
					//Now we append the expressions for each of the arguments in order
					for (int i = 0; i < args.getLength(); i++) {
						pre.appendChild(args.item(i).cloneNode(true));
						System.out.println("Adding argument..*************************");
					}
					//Here we add the actual function body
					
					Element mybody =(Element) functions.get(idx).getElementsByTagName("functionBody").item(0).cloneNode(true);
					pre.appendChild(mybody);
					//Here we update the return calls in mybody
					replaceReturns(mybody, isvoid.get(idx), retlabel, retname); 
					node.getParentNode().replaceChild(pre, node);
					fsm = state.ININSTRUCTION;
				}
				break;
			case INCALL:
				
			break;
			case INNAME:
				if(name == "name"){
					fsm=state.INCALL;
				}
		}
	}
	
	private void rename(Element node, String title){
		/* This routine changes the name of an element as it exists in a tree.
		 * This will not function properly if the node does not have the correct parent.
		 */
		Element element2 = dom.createElement(title);
		// Copy the attributes to the new element 
		NamedNodeMap attrs = node.getAttributes(); 
		for (int i=0; i<attrs.getLength(); i++) { 
			Attr attr2 = (Attr)dom.importNode(attrs.item(i), true); 
			element2.getAttributes().setNamedItem(attr2); 
		} 
		// Move all the children 
		while (node.hasChildNodes()) { 
			element2.appendChild(node.getFirstChild()); 
		} 
		node.getParentNode().replaceChild(element2, node);
	}
	private void replaceReturns(Element node, boolean isvoid, String label, String retval){
		/* 
		 * This method recursively process the entire tree, changing the return values as it goes.
		 * The label name should only be the label given to the exit portion of the function
		 * It sets the return value if it needs one.
		 */
		if(node.getNodeName().equals("return")){
			Element pre = dom.createElement("pre");
			String body;
			if(isvoid){
				body = "{ goto "+label+";}\n";
			}else{
				body = "{"+retval+"=%s; goto "+label+";}\n";
			}
			//We form a pre object for this entry
			pre.appendChild(dom.createTextNode(body));
			if(!isvoid){
				//pre.appendChild(node.getChildNodes().item(0).cloneNode(true));
				pre.appendChild(node.getElementsByTagName("expression").item(0).cloneNode(true));
			}
			//Here we copy the child objects over
			//for(int i=0;i<node.getElementsByTagName("expression").getLength();i++){
				
			//}
			node.getParentNode().replaceChild(pre, node);
		}else{
			NodeList nodeLst = node.getChildNodes();
			for (int s = 0; s < nodeLst.getLength(); s++) {
			    if(nodeLst.item(s).getNodeType() == Node.ELEMENT_NODE){
			    	//System.out.println(nodeLst.item(s));
			    	Element fstNode = (Element) nodeLst.item(s);
			    	replaceReturns(fstNode, isvoid, label, retval);
			    }
			}
		}
	}
	public void process(){
		try {
		  File file = new File(infile);
		  DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
		  DocumentBuilder db = dbf.newDocumentBuilder();
		  dom = db.parse(file);
		  dom.getDocumentElement().normalize();
		  //Here we run our first visitor on it
		  parsedom(dom);
		  //Now save the output
		  
		  System.out.println(dom.toString());
		  DOMSource source = new DOMSource(dom);
		  StreamResult result = new StreamResult(new FileWriter(outfile));
		   // Use a Transformer for output
		  TransformerFactory tFactory =
		    TransformerFactory.newInstance();
		  Transformer transformer = tFactory.newTransformer();

		  transformer.transform(source, result); 
		} catch (Exception e) {
		    e.printStackTrace();
		}
	}
}
