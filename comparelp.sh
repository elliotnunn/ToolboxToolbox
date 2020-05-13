#!/bin/bash

set -m

~/Documents/mac/slow/lpch/patch_rip.py ~/Documents/mac/supermario/worktree/cube-e/BuildResults/System/System.rdump -pj -w 64 -sh ~/Documents/mac/supermario/worktree/cube-e/BuildResults/System/Text/LinkPatchJumpTbl >/tmp/elliot && ~/Documents/mac/slow/lpch/patch_rip.py ~/Documents/mac/primary/Sys710x.rdump -pj -w 64 -sh ~/Documents/mac/supermario/worktree/cube-e/BuildResults/System/Text/LinkPatchJumpTbl >/tmp/apple && git diff --no-index -U999999999 /tmp/elliot /tmp/apple >/tmp/lpch.patch
