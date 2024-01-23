#! /usr/bin/env python

# ptags
#
# Create a tags file for Python programs, usable with vi.
# Tagged are:
# - functions (even inside other defs or classes)
# - classes
# - filenames
# Warns about files it cannot open.
# No warnings about duplicate tags.

import os
import re
import sys

from pathlib import Path

tags = []    # Modified global variable!

def main():
    args = sys.argv[1:]
    for filename in args:
        treat_file(filename)
    if tags:
        # fp = open('tags', 'w')
        # tags.sort()
        # for s in tags: fp.write(s)
        for s in tags: print(s)


expr = '^[ \t]*(def|class)[ \t]+([a-zA-Z0-9_]+)[ \t]*[:\(]'
matcher = re.compile(expr)
matcher = re.compile(r"""
    ^
    (?P<indent> [ \t]* )
    (?:
        (?P<class>
            class
            [ \t]+
            (?P<class_name> [a-zA-Z0-9_]+ )
            [ \t]*
            [:\(]
        )
    |
        (?P<function>
            def
            [ \t]+
            (?P<function_name> [a-zA-Z0-9_]+ )
            [ \t]*
            \(
        )
    |
        (?P<variable>
            (?P<variable_name> [a-zA-Z0-9_]+ )
            [ \t]*
            =
        )
    )
""", re.VERBOSE)

def treat_file(filename):
    if not Path(filename).exists():
        return
    with open(filename, 'r') as fp:
        stack = [ (-1, None, None, True) ]
        for num, line in enumerate(fp, start=1):
            if m :=  matcher.match(line):
                while len(m['indent']) <= stack[-1][0]:
                    stack.pop()
                p_indent, p_name, p_scope, p_contains = stack[-1]
                if not p_contains:
                    continue
                if p_name:
                    parent = f'\t{p_scope}:{p_name}'
                else:
                    parent = ''
                indent = len(m['indent'])
                if m['class']:
                    name = m['class_name'] + " : class"
                    kind = 'h'
                    stack.append((indent, name, 'funnyscope', True))
                elif m['function']:
                    name = m['function_name'] + " : function"
                    if p_name:
                        kind = 'm'
                        stack.append((indent, name, 'member', False))
                    else:
                        kind = 'h'
                        stack.append((indent, name, 'funnyscope', False))
                elif m['variable']:
                    name = m['variable_name']
                    if p_name:
                        kind = 'm'
                    else:
                        kind = 'v'
                content = m.group(0)
                tags.append(f'{name}\t{filename}\t/^{content}/;"\t{kind}{parent}')

def old_treat_file(filename):
    try:
        fp = open(filename, 'r')
    except:
        sys.stderr.write('Cannot open %s\n' % filename)
        return
    base = os.path.basename(filename)
    if base[-3:] == '.py':
        base = base[:-3]
    s = base + '\t' + filename + '\t' + '1\n'
    tags.append(s)
    while 1:
        line = fp.readline()
        if not line:
            break
        m = matcher.match(line)
        if m:
            content = m.group(0)
            name = m.group(2)
            extra = ';"\tf'
            s = name + '\t' + filename + '\t/^' + content + '/' + extra + '\n'
            tags.append(s)

if __name__ == '__main__':
    main()
