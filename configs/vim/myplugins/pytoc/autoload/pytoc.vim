pythonx import vim
pythonx from pytoc import pytoc

function! pytoc#open() abort
    pythonx pytoc.toc()
endfunction
