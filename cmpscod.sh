#!/bin/sh

n=$1
shift
o=$n
if [ "$#" != "0" ]; then o=$1; fi
Rez -o /tmp/ascod ~/MacSrc/Sys710.rdump 2>/dev/null
zcp /tmp/ascod//scod/$n /tmp/ascod$n
#zcp ~/MacFiles/System711//scod/$n /tmp/ascod$n
Rez -o /tmp/bscod BuildResults/System/Rsrc/System.rsrc.rdump
zcp /tmp/bscod//scod/$o /tmp/bscod$o

exec vbindiff /tmp/ascod$n /tmp/bscod$o

# NB: These truly are the sources to System 7.1, plus a tiny bit of sugar.