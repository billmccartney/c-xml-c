rm -rf ./ocaml-3.09.3
tar -xvzf ./3.09.3.tar.gz
cd ocaml-3.09.3/
./configure -host i686-pc-linux-gnu
make world
make opt
make install

