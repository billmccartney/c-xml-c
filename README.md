# C-XML-C - Source to Source translation for C

C-XML-C: A flexible source-to-source C compiler framework which is language
and platform independent. It also includes a series of example compilers to
remove faults and optimize embedded system software.

This is a project which was originally developed as part of 2011 research included in this [paper](https://engagedscholarship.csuohio.edu/etdarchive/196/)

As of 2022 we have setup the entire build system in a docker container so it can be easily accessible.

# Quickstart
TK

# Building the Container
Clone this repository and then run _docker build -t cxmlc ._

This is a multistaged build which compiles a patched version of [CIL](https://github.com/cil-project/cil/).   

# Running
To run the container _docker run -it cxmlc bash_, use "wrapper.py" as you would your compiler.

For example _wrapper.py test.c_ will perform all steps needed to compile test.c including:
* Preprocessing using native compiler
* Translating to XML
* Performing one or more transforms specified by config.ini (null transform is performed by default)
* Translating back to C
* Compiling to a binary

# Usage
tk
## Config Files
tk

## Transformations
There are several example transformations described in this [paper](https://engagedscholarship.csuohio.edu/etdarchive/196/). They can be found in the ./transforms folder.

# License
3-Clause BSD -- see LICENSE.txt for details

# Outside Components
There are a few parts of this outside of the license:

* CIL: Team of CIL, http://www.eecs.berkeley.edu/~necula/cil/
* CIL-XML dumping: J.A. Meister et al, http://www.cs.umd.edu/projects/PL/scil/
* CIL-TinyOS: Nathan Cooprider et al, http://www.cs.utah.edu/~coop/research/tools/