" vi: nowrap textwidth=0

"------------------------------------------------------------------------------------
"-                                                                                  -
"-  Compilation and errors                                                          -
"-                                                                                  -
"------------------------------------------------------------------------------------

let b:use_synctex = 0

let b:tex_file = expand('%:p')
let b:pdf_file = expand('%:p:r').'.pdf'
let b:synctex_file = expand('%:p:r').'.synctex.gz'
let b:synctex_dir = expand('%:p:h')
let b:use_synctex_dir = 0

" " This uses just rubber
" let &makeprg='rubber --pdf -c "set program pdflatex-synctex" %<'
" 
" " This uses both latexmk and rubber-info, the best of both worlds!
" let &makeprg='echo Running latexmk %<'
" let &makeprg.='; latexmk -pdf -pdflatex="pdflatex -synctex=1 \%O \%S" -silent %<'
" " let &makeprg.=' >/dev/null 2>&1 '
" let &makeprg.='; echo '
" let &makeprg.='; rubber-info --errors %<'
" 
" " This uses texcompile, my own program
" let &makeprg='texcompile %<'
" 
" " Use texcompile to get main tex_file
" let s:tc_output = system('texcompile -f ' . shellescape(b:tex_file))
" if ! v:shell_error
"     let b:tex_file = split(s:tc_output, "\n")[0]
"     "let b:pdf_file = fnamemodify(b:tex_file, ':r') . '.pdf'
"     let b:pdf_file = split(s:tc_output, "\n")[1]
" endif
"
" setlocal errorformat=%f:%l:\ %m,%f:\ %m

function! s:SetupLatTeXMk(use_synctex)
    if a:use_synctex == 2
        if filereadable(b:synctex_file)
            let b:use_synctex = 1
        else
            let b:synctex_dir = expand('%:p:h').'/.aux'
            let b:synctex_file = b:synctex_dir.'/'.expand('%:p:t:r').'.synctex.gz'
            if filereadable(b:synctex_file)
                let b:use_synctex = 1
                let b:use_synctex_dir = 1
            elseif filereadable(b:pdf_file)
                let b:use_synctex = 0
            else
                let b:use_synctex = 1
            endif
        endif
    else
        let b:use_synctex = a:use_synctex
    endif
    let &makeprg='echo Running latexmk;'
    let &makeprg.=' latexmk'
    let &makeprg.=' -verbose'
    let &makeprg.=' -file-line-error'
    if b:use_synctex == 1
        let &makeprg.=' -synctex=1'
    endif
    let &makeprg.=' -interaction=nonstopmode'

    if filereadable('.latexmkrc') || filereadable('latexmkrc') || filereadable('platexmkrc')
        if filereadable('platexmkrc')
            let &makeprg.=' -pdf'
            let &makeprg.=' -r platexmkrc'
        endif
    else
        let &makeprg.=' -pdf'
        let &makeprg.=' -aux-directory=.aux'
        let &makeprg.=' -emulate-aux-dir'
        let &makeprg.=' -recorder-'
        let &makeprg.=' %<'
    endif
endfunction

call s:SetupLatTeXMk(2)

" Match file name
setlocal errorformat=%-P**%f
setlocal errorformat+=%-P**\"%f\"

" Match LaTeX errors
setlocal errorformat+=%E!\ LaTeX\ %trror:\ %m
setlocal errorformat+=%E%f:%l:\ %m
setlocal errorformat+=%E!\ %m

" More info for undefined control sequences
setlocal errorformat+=%Z<argument>\ %m

" More info for some errors
setlocal errorformat+=%Cl.%l\ %m

" Catch-all to ignore unmatched lines
setlocal errorformat+=%-G%.%#

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

"------------------------------------------------------------------------------------
"-                                                                                  -
"-  Commands                                                                        -
"-                                                                                  -
"------------------------------------------------------------------------------------

let b:tex_viewer_opened = 0
let s:use_skim = 0
let s:skim_display_line = expand("<sfile>:p:h") . "/skim_display_line"
let s:use_aViewer = 1
let s:aViewer_synctex = "open -n -a aViewer.app --args --synctex"
let s:aViewer_open = "open -a aViewer.app"

function! s:TexView(open)
  if has('mac') && (s:use_skim==1) && (b:tex_viewer_opened==1 || a:open==1)
    let b:tex_viewer_opened = 1
    let l:cmd = s:skim_display_line
    let l:cmd.= ' -r'
    if (a:open==0)
      let l:cmd.= ' -g -x'
    endif
    let l:cmd.= ' ' . line('.')
    " let l:cmd.= ' "' . b:pdf_file . '"'
    " let l:cmd.= ' "' . b:tex_file . '"'
    let l:cmd.= ' ' . shellescape(b:pdf_file)
    let l:cmd.= ' ' . shellescape(b:tex_file)
    let l:output = system(l:cmd)
  elseif has('mac') && (s:use_aViewer==1) && (b:tex_viewer_opened==1 || a:open==1)
    if b:tex_viewer_opened == 0
      let b:tex_viewer_opened = 1
      " open pdf in aViewer
      let l:cmd = s:aViewer_open
      let l:cmd.= ' ' . shellescape(b:pdf_file)
      let l:output = system(l:cmd)
    else
      " sync aViewer position
      let l:cmd = s:aViewer_synctex
      let l:cmd.= ' ' . line('.')
      let l:cmd.= ' ' . col('.')
      let l:cmd.= ' ' . shellescape(b:tex_file)
      let l:cmd.= ' ' . shellescape(b:pdf_file)
      if b:use_synctex_dir == 1
          let l:cmd.= ' ' . shellescape(b:synctex_dir)
      endif
      let l:output = system(l:cmd)
      " bring aViewer to front
      " let l:cmd = s:aViewer_open
      " let l:cmd.= ' ' . shellescape(b:pdf_file)
      " let l:output = system(l:cmd)
    endif
  endif
endf

function! s:TexAuxConfigXAttr()
    if filewritable('.aux') == 2
        if has('mac')
            let l:ret = system('xattr -w com.dropbox.ignored 1 .aux')
        else
            let l:ret = system('attr -s com.dropbox.ignored -V 1 .aux')
        endif
    endif
endfunction

function! s:TexAuxCleanup()
    if b:use_synctex == 0
        if filereadable(b:synctex_file)
            call delete(b:synctex_file)
        endif
    endif
    call delete('.aux', 'd')
    call s:TexAuxConfigXAttr()
endfunction

function! s:TexCompile()
    call s:TexAuxConfigXAttr()
    write
    silent make!
    let l:err=0
    for l:m in getqflist()
        if l:m.valid
            let l:err=1
            break
        endif
    endfor
    call s:TexAuxCleanup()
    botright cwindow
    if !(l:err)
        call s:TexView(0)
    endif
    redraw!
endfunction

command! -nargs=* TexView call s:TexView(<f-args>)
command! TexCompile call s:TexCompile()
command! Synctex call s:SetupLatTeXMk(1)
command! NoSynctex call s:SetupLatTeXMk(0)

nnoremap <buffer> <space><space> :TexCompile<cr>
nnoremap <buffer> <leader><leader> :TexView 1<cr>
nnoremap <buffer> <leader>s :Synctex<cr>
