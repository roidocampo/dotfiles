pythonx import vim
pythonx import inb

function! inb#RunCell() abort
    pythonx inb.run_cell()
endfunction

sign define inbCellHead text=%% texthl=CellHead linehl=CellHead
sign define inbOutputCellHead text=%% texthl=OutputCellHead linehl=OutputCellBg
set signcolumn=yes
set spell

augroup inb
    autocmd!
    autocmd VimLeave * pythonx inb.cleanup()
    autocmd BufWinenter *.inb pythonx inb.update_signs()
    autocmd TextChanged *.inb pythonx inb.update_signs()
    autocmd TextChangedI *.inb pythonx inb.update_signs()
    autocmd InsertLeave *.inb pythonx inb.update_signs()
augroup END

command! -buffer -nargs=0 InbRunCell call inb#RunCell()

nnoremap <buffer> <silent> <space><space> :InbRunCell<CR>
