#!/bin/sh

ROMFILE="$(find ~/Documents/mac/MacROMan/TestImages -name '*9779D2C4*.ROM' | head -n1)"

set -e -u -o pipefail

cd $1

echo '#define kMaintainerName "Elliot build box"' >setup/CONFIGUR.i

gcc setup/tool.c -o setup_t
./setup_t -t mc64 -m II -speed a -bg 1 -as 0 >setup_buildbox.bash

chmod +x setup_buildbox.bash
./setup_buildbox.bash
make

mkdir -p ~/Documents/buildmac
rm -rf ~/Documents/buildmac/{minivmac,MacII.ROM}
cp -R minivmac.app ~/Documents/buildmac/
cp "$ROMFILE" ~/Documents/buildmac/MacII.ROM
