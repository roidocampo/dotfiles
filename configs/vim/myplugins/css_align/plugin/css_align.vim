function CSSAlign(sep)
    let l:winview = winsaveview()
    let l:firstline = search('\({\|\}\)','bcnW')
    let l:lastline = search('\({\|\}\)','cnW')
    if (l:firstline != 0) 
                \&& (l:lastline != 0)
                \&& ((l:firstline+1) < (l:lastline-1))
        execute (l:firstline+1)
                    \. ',' 
                    \. (l:lastline-1)
                    \. 'Tabularize /'
                    \. a:sep
    endif
    call winrestview(l:winview)
    echom "hola <" . l:firstline . ',' . l:lastline . '>'
endfunction
