if exists("b:current_syntax")
  finish
endif

syntax include @Python syntax/python.vim
unlet b:current_syntax
syntax include @Markdown syntax/markdown.vim
unlet b:current_syntax
syntax include @Singular syntax/singular.vim
unlet b:current_syntax
syntax include @Macaulay2 syntax/Macaulay2.vim
unlet b:current_syntax

syntax region MardownCell matchgroup=CellHead start=/^%%\(-\? \s*\(md\|[mM]arkdown\)\s*\|\s*\)$/ end=/^%%/re=s,me=s-1 contains=@Markdown,@Spell
syntax region MardownCell matchgroup=CellHead start=/\%^/ end=/^%%/re=s,me=s-1 contains=@Markdown,@Spell
syntax region PythonCell matchgroup=CellHead start=/^%%-\? \s*\([pP]y\(thon\)\?[23]\?\|[sS]age\|sg\)\( .*\)\?$/ end=/^%%/re=s,me=s-1 contains=@Python
syntax region SingularCell matchgroup=CellHead start=/^%%-\? \s*\(sing\|[sS]ingular\)\( .*\)\?$/ end=/^%%/re=s,me=s-1 contains=@Singular
syntax region Macaulay2Cell matchgroup=CellHead start=/^%%-\? \s*\([mM]2\|[mM]acaulay2\)\( .*\)\?$/ end=/^%%/re=s,me=s-1 contains=@Macaulay2
syntax region OutputCell matchgroup=OutputCellHead start=/^%%-\? \s*out/ end=/^%%/re=s,me=s-1

hi CellHead ctermfg=17 ctermbg=18
hi OutputCellHead ctermfg=17 ctermbg=18
hi OutputCell ctermfg=8
hi OutputCellBg ctermbg=18

let b:current_syntax = "inb"
