#!/bin/sh

set -euo pipefail

rm -rf /tmp/SheepShaver7
mkdir /tmp/SheepShaver7
cp ~/Documents/mac/supermario/worktree/cube-e/BuildResults/System/System* /tmp/SheepShaver7/
cp ~/Downloads/MacsBug\ 6.2.2/* /tmp/SheepShaver7/
cp ~/Documents/mac/slow/sev-fun/Finder* /tmp/SheepShaver7/

MakeHFS -n SheepShaver7 -i /tmp/SheepShaver7 -s 20m -d now /tmp/SheepShaver7.dsk
