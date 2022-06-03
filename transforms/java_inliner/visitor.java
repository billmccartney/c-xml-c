import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.w3c.dom.Document;


public class visitor {
	Document dom;
	public void parsedom(Document mydom){
		dom = mydom;
		NodeList nodeLst = mydom.getChildNodes();
		for (int s = 0; s < nodeLst.getLength(); s++) {
		    if(nodeLst.item(s).getNodeType() == Node.ELEMENT_NODE){
		    	//System.out.println(nodeLst.item(s));
		    	Element fstNode = (Element) nodeLst.item(s);
		    	pass(fstNode);
		    }
		}
	}
	private void pass(Element node){
		enter(node);
		NodeList nodeLst = node.getChildNodes();
		for (int s = 0; s < nodeLst.getLength(); s++) {
		    if(nodeLst.item(s).getNodeType() == Node.ELEMENT_NODE){
		    	//System.out.println(nodeLst.item(s));
		    	Element fstNode = (Element) nodeLst.item(s);
		    	pass(fstNode);
		    }
		}
		leave(node);
	}
	public void enter(Element node){
		
	}
	public void leave(Element node){
		
	}
}
