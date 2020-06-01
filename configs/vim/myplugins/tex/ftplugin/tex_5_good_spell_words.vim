
if exists("s:good_words_loaded")
    finish
endif
let s:good_words_loaded = 1

function s:InitialAddGoodWords()
    while search('LocalWords\s*:','W')
        let l:sline = getline('.')
        let l:slineend = matchstr(l:sline, ':\s*\zs.*')
        let l:words = split(l:slineend)
        for l:word in l:words
            silent execute 'spellgood!' l:word
        endfor
    endwhile
endfunction

call s:InitialAddGoodWords()

function s:AddGoodWord()
    let l:winview = winsaveview()
    let l:prev_fold = &foldenable
    if l:prev_fold
        set nofoldenable
    endif
    let l:word = expand("<cWORD>")
    normal G$
    let l:vsg_line_num = search('LocalWords\s*:',"bW")
    if l:vsg_line_num == 0
        execute "normal o% LocalWords:\e" 
    else
        let l:vsg_line = getline(l:vsg_line_num)
        if len(l:vsg_line) > 65
            execute "normal o% LocalWords:\e" 
        endif
    endif
    execute "normal A ". l:word ."\e" 
    silent execute 'spellgood!' l:word
    if l:prev_fold
        set foldenable
    endif
    call winrestview(l:winview)
endfunction

nmap <LocalLeader>g :call <SID>AddGoodWord()<CR>
