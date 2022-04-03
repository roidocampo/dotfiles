" vi: nowrap textwidth=0

"------------------------------------------------------------------------------------
"-                                                                                  -
"-  Compilation and errors                                                          -
"-                                                                                  -
"------------------------------------------------------------------------------------

" This uses just rubber
let &makeprg='rubber --pdf -c "set program pdflatex-synctex" %<'

" This uses both latexmk and rubber-info, the best of both worlds!
let &makeprg='echo Running latexmk %<'
let &makeprg.='; latexmk -pdf -pdflatex="pdflatex -synctex=1 \%O \%S" -silent %<'
" let &makeprg.=' >/dev/null 2>&1 '
let &makeprg.='; echo '
let &makeprg.='; rubber-info --errors %<'

" This uses texcompile, my own program
let &makeprg='texcompile %<'

let b:tex_file = expand('%:p')
let b:pdf_file = expand('%:p:r').'.pdf'

" Use texcompile to get main tex_file
let s:tc_output = system('texcompile -f ' . b:tex_file)
if ! v:shell_error
    let b:tex_file = split(s:tc_output, "\n")[0]
    "let b:pdf_file = fnamemodify(b:tex_file, ':r') . '.pdf'
    let b:pdf_file = split(s:tc_output, "\n")[1]
endif

if filereadable('makefile') || filereadable('Makefile')
  let s:output = system('make -n fromvim')
  if ! v:shell_error
    let &makeprg='make "VIMSERVER='.v:servername.'" "VIMFILE='.expand('%p').'" fromvim'
  endif
  let s:output = system('make "VIMFILE='.expand('%p').'" fromvim-conf')
  if ! v:shell_error
    let b:pdf_file = split(s:output)[0]
  endif
endif

setlocal errorformat=%f:%l:\ %m,%f:\ %m

"------------------------------------------------------------------------------------
"-                                                                                  -
"-  Commands                                                                        -
"-                                                                                  -
"------------------------------------------------------------------------------------

let b:tex_viewer_opened = 0
let s:skim_display_line = expand("<sfile>:p:h") . "/skim_display_line"

function! s:TexView(open)
  if has('mac') && (b:tex_viewer_opened==1 || a:open==1)
    let b:tex_viewer_opened = 1
    let l:cmd = s:skim_display_line
    let l:cmd.= ' -r'
    if (a:open==0)
      let l:cmd.= ' -g -x'
    endif
    let l:cmd.= ' ' . line('.')
    let l:cmd.= ' "' . b:pdf_file . '"'
    let l:cmd.= ' "' . b:tex_file . '"'
    let l:output = system(l:cmd)
  endif
endf

function! s:TexCompile()
  write
  silent make!
  let l:err=0
  for l:m in getqflist()
    if l:m.valid
      let l:err=1
      break
    endif
  endfor
  botright cwindow
  if !(l:err)
    call s:TexView(0)
  endif
  redraw!
endfunction

command! -nargs=* TexView call s:TexView(<f-args>)
command! TexCompile call s:TexCompile()

nnoremap <buffer> <space><space> :TexCompile<cr>
nnoremap <buffer> <leader><leader> :TexView 1<cr>
