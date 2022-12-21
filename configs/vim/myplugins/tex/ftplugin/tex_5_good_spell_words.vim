
if exists("s:good_words_loaded")
    finish
endif
let s:good_words_loaded = 1

let s:lw_addfile = '.localwords.utf-8.add'
let s:lw_splfile = s:lw_addfile . '.spl'

let s:has_local_words = 0
function s:InitialAddGoodWords()
    while search('LocalWords\s*:','W')
        let s:has_local_words = 1
        let l:sline = getline('.')
        let l:slineend = matchstr(l:sline, ':\s*\zs.*')
        let l:words = split(l:slineend)
        for l:word in l:words
            silent execute 'spellgood!' l:word
        endfor
    endwhile
    if s:has_local_words == 0
        let &spellfile = s:lw_addfile
    endif
endfunction

function s:AddGoodWord()
    let l:winview = winsaveview()
    let l:prev_fold = &foldenable
    if l:prev_fold
        set nofoldenable
    endif
    let l:word = expand("<cword>")
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

function s:FirstAddGoodWord()
    if s:has_local_words == 0
        if !filereadable(s:lw_addfile)
            if has('mac')
                let l:ret = system('touch ' . s:lw_addfile)
            endif
        endif
        if !filereadable(s:lw_splfile)
            if has('mac')
                let l:ret = system('touch ' . s:lw_splfile)
            endif
        endif
        let l:ret = system('xattr -w com.dropbox.ignored 1 ' . s:lw_addfile)
        let l:ret = system('xattr -w com.dropbox.ignored 1 ' . s:lw_splfile)
        nmap <LocalLeader>g zg
        normal zg
    else
        nmap <LocalLeader>g :call <SID>AddGoodWord()<CR>
        call s:AddGoodWord()
    endif
endfunction

let s:output = system('git rev-parse --show-toplevel')
if ! v:shell_error
    let &spellfile = split(s:output, "\n")[0] . s:lw_addfile
    nmap <LocalLeader>g zg
else
    call s:InitialAddGoodWords()
    nmap <LocalLeader>g :call <SID>FirstAddGoodWord()<CR>
endif
