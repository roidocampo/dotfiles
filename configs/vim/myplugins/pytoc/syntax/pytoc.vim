
highlight C_GRAY ctermfg=8
highlight C_GREEN ctermfg=2
highlight C_PINK ctermfg=16
highlight C_PURPLE ctermfg=17
highlight C_ORANGE ctermfg=13
highlight C_BLUE ctermfg=4
highlight C_YELLOW ctermfg=3
highlight C_YELLOW_GREEN ctermfg=2


syntax match PyTocFunction "^\s*\zs\h\w*\ze\s*()"
syntax match PyTocClass "^\s*\zs\h\w*\ze\s*\:"
syntax match PyTocSeparator "^=\+\s*$"
syntax match PyTocSubSection "^\s*\[.*\]\s*"
syntax match PyTocSection "^\(\h\|@\).*$"
syntax match PyTocTitle "\%^.*$"

highlight link PyTocClass C_BLUE
highlight link PyTocFunction C_BLUE
highlight link PyTocSection C_PURPLE
highlight link PyTocSubSection C_GRAY
highlight link PyTocSeparator C_YELLOW
highlight link PyTocTitle C_ORANGE
