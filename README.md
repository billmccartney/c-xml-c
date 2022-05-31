# C-XML-C
C-XML-C - Source to Source translation for C

This is being upgraded to support UnStackedC.

We have setup the entire system in a docker container which can be used for compiling
# Build
Clone this repository and then run _docker build -t cxmlc ._

This is a multistaged build which compiles a patched version of [CIL](https://github.com/cil-project/cil/) and it includes  

# Running
To run the container _docker run -it cxmlc bash_, use "wrapper.py" as you would your compiler.

For example _wrapper.py test.c_ will perform all steps needed to compile test.c including:
* Preprocessing using native compiler
* Translating to XML
* Performing the transform (stackless.py by default)
* Translating back to C
* Compiling to a binary

# Usage
tk
## Config Files
tk