
" Block math. Look for "$$[anything]$$"
syntax region MathBlock start="\\\@<!\$\$" end="\$\$" skip="\\\$" contains=@NoSpell,MathCommand,MathDelimiter keepend
syntax region MathBlock start="\\\@<!<span[^>]*>" end="</span>" contains=@NoSpell,MathCommand,MathDelimiter,MathSpan,MathClass keepend

" inline math. Look for "$[not $][anything]$"
syntax match MathInline '\$[^$].\{-}\$' contains=@NoSpell,MathCommand,MathDelimiter

syntax match MathDelimiter "\(\$\|&\|\^\|\\qq*uad\|{\|}\)" contains=@NoSpell contained
syntax match MathCommand "\\\S\(\a\|@\)*" contains=@NoSpell contained
syntax match MathSpan "span" contains=@NoSpell contained
syntax match MathClass "class" contains=@NoSpell contained

"hi link math yamlEscape
"hi link math_block yamlEscape

highlight C_GRAY ctermfg=8
highlight C_GREEN ctermfg=2
highlight C_PINK ctermfg=16
highlight C_PURPLE ctermfg=17
highlight C_ORANGE ctermfg=13
highlight C_BLUE ctermfg=4
highlight C_YELLOW ctermfg=3
highlight C_YELLOW_GREEN ctermfg=2

highlight link MathDelimiter C_GRAY
highlight link MathCommand C_PINK
highlight link MathSpan htmlTagName
highlight link MathClass htmlArg
