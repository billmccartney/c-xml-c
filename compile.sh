rm -rf ./cil-cil-1.3.6
tar -xvzf ./cil-1.3.6.tar.gz
cd cil-cil-1.3.6
patch -p1 < ../cil-embedded.patch
patch -p1 < ../writexml.patch
cd src
rm -f machdep.c
ln -s machdep-native.c machdep.c
cd frontc
rm -f cabs2cil.ml
ln -s cabs2cil-native.ml cabs2cil.ml
cd ../../
autoconf
./configure
make
cd ..
cp cil-cil-1.3.6/obj/x86_LINUX/cilly.asm.exe ./cilly.native

rm -rf ./cil-cil-1.3.6
tar -xvzf ./cil-1.3.6.tar.gz
cd cil-cil-1.3.6
patch -p1 < ../cil-embedded.patch
patch -p1 < ../writexml.patch
cd src
rm -f machdep.c
ln -s machdep-avr.c machdep.c
cd frontc
rm -f cabs2cil.ml
ln -s cabs2cil-avr.ml cabs2cil.ml
cd ../../
autoconf
./configure --target=avr
make
cd ..
cp cil-cil-1.3.6/obj/avr_EMBEDDED/cilly.asm.exe ./cilly.avr


rm -rf ./cil-cil-1.3.6
tar -xvzf ./cil-1.3.6.tar.gz
cd cil-cil-1.3.6
patch -p1 < ../cil-embedded.patch
patch -p1 < ../writexml.patch
cd src
rm -f machdep.c
ln -s machdep-msp430.c machdep.c
cd frontc
rm -f cabs2cil.ml
ln -s cabs2cil-msp430.ml cabs2cil.ml
cd ../../
autoconf
./configure --target=msp430
make
cd ..
cp cil-cil-1.3.6/obj/msp430_EMBEDDED/cilly.asm.exe ./cilly.msp430
