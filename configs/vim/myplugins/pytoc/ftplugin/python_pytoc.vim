command! -buffer -nargs=0 PyTocOpen call g:pytoc#open()

nnoremap <buffer> <silent> <F6> :PyTocOpen<CR>
