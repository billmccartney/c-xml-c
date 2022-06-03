//import java.io.*;

public class java_inline {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		xml_visitor t; 
		if(args.length < 2){
			System.out.println("usage:\n java_inline input.xml output.xml\n");
		}
		
		t = new xml_visitor(args[0], args[1]);
		t.process();
	}
}
