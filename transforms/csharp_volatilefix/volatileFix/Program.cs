using System;
using System.Collections.Generic;
using System.Text;
using System.Xml;


namespace volatileFix
{
    class Program
    {
        static void Main(string[] args)
        {
            XmlDocument myXmlDocument = new XmlDocument();
            Processor p;
            if (args.Length < 2)
            {
                Console.WriteLine("Usage:");
                Console.WriteLine("  volatileFix input.xml output.xml");
            }
            myXmlDocument.Load(args[0]);
            p = new Processor(ref myXmlDocument);
            p.Process();
            myXmlDocument.Save(args[1]);
        }
    }
    class Processor
    {
        public XmlDocument myxml;
        List<string> reads;
        List<string> writes;
        List<string> calls;
        List<MyFunction> functions = new List<MyFunction>();
        enum States { Idle, Assignment, Call, CallerName };
        enum MStates { Idle, Decl, Type };
        States state;
        MStates mstate;
        List<string> conflicts;
        public Processor(ref XmlDocument input)
        {
            myxml = input;
            state = States.Idle;
        }

        public void Process()
        {
            List<String> main = new List<string>();
            List<String> remains = new List<string>();
            conflicts = new List<string>();

            pass1(myxml);
            foreach (MyFunction f in functions)
                f.overall(functions);
            functions[0].markMain();
            //So now build up the larger lists
            foreach (MyFunction f in functions)
            {
                main.AddRange(f.mainRead());
                remains.AddRange(f.remainWrite());
            }
            main = unique(main);
            remains = unique(remains);
            //Now we compare to find conflicts
            foreach (string s in main)
                foreach (string t in remains)
                    if (s == t)
                        conflicts.Add(s);
            Console.WriteLine("Conflicts...");
            foreach (string s in conflicts)
                Console.WriteLine(s);
            //foreach (MyFunction f in functions)
            //    f.print();
            pass2(myxml);
        }
        private void pass1(XmlNode node)
        {
            //Here we just build up a call graph and a list of global variable accesses
            foreach (XmlNode child in node.ChildNodes)
            {
                if (child.NodeType == XmlNodeType.Element)
                {
                    if (child.Name == "functionDefinition")
                    {
                        StartSearching(child);
                    }
                    else
                    {
                        pass1(child);
                    }
                }

            }
        }
        private void pass2(XmlNode node)
        {
            mstate = MStates.Idle;
            Modifying(node);
        }
        private void Modifying(XmlNode node)
        {
            MStates last = mstate;
            switch (mstate)
            {
                case MStates.Idle:
                    if (node.Name == "variableDefinition")
                        if(conflicts.Contains(node.Attributes["name"].Value))
                            mstate = MStates.Decl;
                    break;
                case MStates.Decl:
                    if (node.Name == "type")
                        mstate = MStates.Type;
                    break;
                case MStates.Type:
                    if (node.Name == "attribute")
                        if (node.Attributes["name"].Value == "volatile")
                            last = mstate = MStates.Idle;
                    break;
            }
            if ((mstate == MStates.Type) && (last == MStates.Decl))
            {
                XmlNode newxml = myxml.CreateElement("attribute");
                XmlAttribute attr = myxml.CreateAttribute("name");
                attr.Value = "volatile";
                newxml.Attributes.Append(attr);
                node.AppendChild(newxml);
            }
            foreach (XmlNode child in node.ChildNodes)
                Modifying(child);
            mstate = last;
        }
        private void StartSearching(XmlNode node)
        {
            reads = new List<string>();
            writes = new List<string>();
            calls = new List<string>();
            Searching(node);
            functions.Add(new MyFunction(node.Attributes["name"].Value, reads, writes, calls));
        }
        private void internalSearch(XmlNode node)
        {
            foreach (XmlNode child in node.ChildNodes)
            {
                if (child.NodeType == XmlNodeType.Element)
                {
                    Searching(child);
                }
            }
        }

        private void Searching(XmlNode node)
        {
            States last = state;
            if (node.Name == "functionCall")
            {
                state = States.Call;
            }
            if (node.Name == "instruction")
            {
                if (node.Attributes["kind"].Value == "assignment")
                {
                    foreach (XmlNode n in node.ChildNodes)
                    {
                        if (n.Name == "lvalue")
                        {
                            state = States.Assignment;
                            internalSearch(n);
                            state = last;
                        }
                        else
                        {
                            internalSearch(n);
                            state = last;
                        }
                    }

                }
            }
            else if (state == States.Call)
            {
                if (node.Name == "name")
                {
                    state = States.CallerName;
                }
            }
            else if (node.Name == "variableUse")
            {
                if (state == States.Assignment)
                {
                    if (node.Attributes["isGlobal"].Value == "true")
                        writes.Add(node.Attributes["name"].Value);
                }
                else if (state == States.CallerName)
                {
                    calls.Add(node.Attributes["name"].Value);
                }
                else
                {
                    //if (node.Attributes["isGlobal"].Value == "true")
                    reads.Add(node.Attributes["name"].Value); //reads.Add(node.Attributes("name"));
                }
            }
            internalSearch(node);
            state = last;
        }

        private void FindingFaults()
        {
            int i;
            //Here we search through the data saved for any errors
            for (i = 0; i < functions.Count; i++)
            {

            }
        }


        public List<string> unique(List<string> input)
        {
            Dictionary<string, int> uniqueStore = new Dictionary<string, int>();
            List<string> finalList = new List<string>();
            foreach (string currValue in input)
            {
                if (!uniqueStore.ContainsKey(currValue))
                {
                    uniqueStore.Add(currValue, 0);
                    finalList.Add(currValue);
                }
            }
            return finalList;

        }
    }
    class MyFunction
    {
        private List<string> reads, writes, calls;
        private List<MyFunction> total;
        public string name;
        public bool inMain = false;
        public MyFunction(string nname, List<string> nreads, List<string> nwrites, List<string> ncalls){
            name = nname;
            reads = nreads;
            writes = nwrites;
            calls = ncalls;
        }

        public void overall(List<MyFunction> totalFunctions){
            total = totalFunctions;
        }

        public bool isname(string cmpName)
        {
            return cmpName == name;
        }

        public void markMain()
        {
            graph("main");
        }
        public List<MyFunction> Main()
        {
            //Here we must find all of the items called (directly or indirectly) from main
            List<MyFunction> result = new List<MyFunction>();
            foreach (MyFunction f in total)
                if (f.inMain)
                    result.Add(f);
            return result;
        }

        public List<MyFunction> Remainder()
        {
            //Here we must find all of the items called (directly or indirectly) from main
            List<MyFunction> result = new List<MyFunction>();
            //graph(name);
            foreach (MyFunction f in total)
                if (!f.inMain)
                    result.Add(f);
            return result;
        }

        public List<string> mainRead()
        {
            return FindReads(Main(), true);
        }
        public List<string> mainWrite()
        {
            return FindWrites(Main(), true);
        }
        public List<string> remainRead()
        {
            return FindReads(Remainder(), false);
        }
        public List<string> remainWrite()
        {
            return FindWrites(Remainder(),false);
        }
        private List<string> FindReads(List<MyFunction> input, bool myMain)
        {
            List<String> result = new List<String>();
            foreach (MyFunction f in input)
                if (f.inMain == myMain)
                    result.AddRange(f.reads);
            return result;
        }
        private List<string> FindWrites(List<MyFunction> input, bool myMain)
        {
            List<String> result = new List<String>();
            foreach (MyFunction f in input)
                if (f.inMain == myMain)
                    result.AddRange(f.writes);
            return result;
        }
        private void graph(string title)
        {
            //Here we find the next one 
            if (name != title)
            {
                foreach (MyFunction f in total)
                {
                    if (f.isname(title))
                    {
                        f.graph(title);
                        return;
                    }
                }
            }
            else
            {
                inMain = true;
                foreach (string s in calls)
                    foreach (MyFunction f in total)
                    {
                        if (f.isname(s))
                        {
                            if (!f.inMain)
                            {
                                f.graph(s);
                            }
                        }
                    }
            }
        }
        public void print(){
            Console.WriteLine(name);
            Console.WriteLine(" inmain "+inMain.ToString());
            Console.WriteLine(" read:");
            foreach (string s in reads)
                Console.WriteLine("   " + s);
            Console.WriteLine(" write:");
            foreach (string s in writes)
                Console.WriteLine("   " + s);
            Console.WriteLine(" calls:");
            foreach (string s in calls)
                Console.WriteLine("   " + s);
        }
    }
}
