#!/bin/sh

# http://hints.macworld.com/article.php?story=20021024064107356

if [ $# -eq 0 ]; then
  echo "Usage: alias2ln alias1 alias2 alias3..."
  echo "  where alias1, alias2, etc are alias files."
  echo "  Each alias file will be converted into a symlink."
fi

while [ $# -gt 0 ]; do
  if [ -f "$1" -a ! -L "$1" ]; then
    item_name=`basename "$1"`
    item_parent=`dirname "$1"`
    # Next two rows should be entered as one row #
    item_parent="`cd \"${item_parent}\" 2>/dev/null && pwd || echo \"${item_parent}\"`"
    item_path="${item_parent}/${item_name}"
    line_1='tell application "Finder"'
    line_2='set theItem to (POSIX file "'${item_path}'") as alias'
    line_3='if the kind of theItem is "alias" then'
    line_4='get the posix path of (original item of theItem as text)'
    line_5='end if'
    line_6='end tell'
    # Next two rows should be entered as one row #
    linksource=`osascript -e "$line_1" -e "$line_2" -e "$line_3" -e "$line_4" -e "$line_5" -e "$line_6"`
    if [ $? -eq 0 ]; then
      if [ ! -z "$linksource" ]; then
        rm "$item_path"
        ln -s "${linksource}" "${item_path}"
        echo "\"${1}\" -> \"${linksource}\""
      fi
    fi
    shift
  fi
done
