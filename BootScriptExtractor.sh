#!/bin/sh

# USAGE: BootScriptExtractor <ROM >BOOTSCRIPT

head -c $((0x4000)) | LC_CTYPE=C tr -d '\0' | LC_CTYPE=C tr '\r' '\n' | awk 'f && /BOOT-SCRIPT/{exit} f{print} /BOOT-SCRIPT/{f=1}' | sed 's/# ...... const/# xxxxxx const/'
