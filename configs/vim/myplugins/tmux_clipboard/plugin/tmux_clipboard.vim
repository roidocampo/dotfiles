
if ( exists('g:loaded_tmux_clipboard') && g:loaded_tmux_clipboard )
    finish
endif

let g:loaded_tmux_clipboard = 1

if !executable('tmux')
    finish
endif

if empty($SSH_CONNECTION)
    set clipboard=unnamedplus
    let s:on_ssh = 0
else
    let s:on_ssh = 1
endif

augroup tmux_clipboard

    autocmd!
    autocmd TextYankPost * call <SID>tmux_clipboard_write()

augroup END

let g:max_osc52_sequence=100000

function s:send_osc52(str)
    let osc52 = s:str_to_osc52(a:str)
    let len = strlen(osc52)
    if len < g:max_osc52_sequence
        call s:rawecho(osc52)
    else
        echomsg "OSC 52 Error. Selection too long to send to terminal: " . len
    endif
endfunction

function s:rawecho(str)
    execute "silent! !echo -n " . shellescape(a:str)
endfunction

function s:str_to_osc52(str)
    let b64 = s:b64encode(a:str)
    let rv = "\e]52;c;" . b64 . "\x07"
    return rv
endfunction

let s:b64_table = [
      \ "A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P",
      \ "Q","R","S","T","U","V","W","X","Y","Z","a","b","c","d","e","f",
      \ "g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v",
      \ "w","x","y","z","0","1","2","3","4","5","6","7","8","9","+","/"]

function s:b64encode(str)
    let bytes = s:str2bytes(a:str)
    let b64 = []
    for i in range(0, len(bytes) - 1, 3)
        let n = bytes[i] * 0x10000
              \ + get(bytes, i + 1, 0) * 0x100
              \ + get(bytes, i + 2, 0)
        call add(b64, s:b64_table[n / 0x40000])
        call add(b64, s:b64_table[n / 0x1000 % 0x40])
        call add(b64, s:b64_table[n / 0x40 % 0x40])
        call add(b64, s:b64_table[n % 0x40])
    endfor
    if len(bytes) % 3 == 1
        let b64[-1] = '='
        let b64[-2] = '='
    endif
    if len(bytes) % 3 == 2
        let b64[-1] = '='
    endif
    return join(b64, '')
endfunction

function s:str2bytes(str)
    return map(range(len(a:str)), 'char2nr(a:str[v:val])')
endfunction

function s:tmux_clipboard_write()

    if !s:on_ssh
        let r = [getreg('"'), getregtype('"')]
    endif

    let lines = get(v:event, "regcontents", [])[:]
    let _ = tempname()
    call writefile(lines, _, 'b')
    call system('tmux load-buffer -b vim ' . shellescape(_))
    call delete(_)

    let regtype = get(v:event, "regtype", [])
    let _ = tempname()
    call writefile([regtype], _, 'b')
    call system('tmux load-buffer -b vimtype ' . shellescape(_))
    call delete(_)

    let text = join(lines, "\n")
    if regtype !=# "v"
        let text .= "\n"
    endif

    call s:send_osc52(text)

    if !s:on_ssh
        call setreg('+', r[0], r[1])
    endif

endfunction

function s:tmux_clipboard_read(reg)
    let cont = systemlist('tmux show-buffer -b vim')
    let regtype = system('tmux show-buffer -b vimtype')
    call setreg(a:reg, cont, regtype)
endfunction

function s:count()
    return (v:count == v:count1) ? v:count : ''
endfunction

function s:put(put_type)
    if !s:on_ssh
        execute 'normal!' s:count() . '"+' . a:put_type
    else
        call s:tmux_clipboard_read('"')
        execute 'normal!' s:count() . '""' . a:put_type
    endif
endfunction

nnoremap <silent> <Plug>(tmux-clipboard-p)  :<C-u>call <SID>put('p')<CR>
nnoremap <silent> <Plug>(tmux-clipboard-P)  :<C-u>call <SID>put('P')<CR>
nnoremap <silent> <Plug>(tmux-clipboard-gp) :<C-u>call <SID>put('gp')<CR>
nnoremap <silent> <Plug>(tmux-clipboard-gP) :<C-u>call <SID>put('gP')<CR>
nnoremap <silent> <Plug>(tmux-clipboard-]p) :<C-u>call <SID>put(']p')<CR>
nnoremap <silent> <Plug>(tmux-clipboard-]P) :<C-u>call <SID>put(']P')<CR>
nnoremap <silent> <Plug>(tmux-clipboard-[p) :<C-u>call <SID>put('[p')<CR>
nnoremap <silent> <Plug>(tmux-clipboard-[P) :<C-u>call <SID>put('[P')<CR>

vnoremap <silent> <Plug>(tmux-clipboard-p)  :<C-u>call <SID>put('p')<CR>
vnoremap <silent> <Plug>(tmux-clipboard-P)  :<C-u>call <SID>put('P')<CR>
vnoremap <silent> <Plug>(tmux-clipboard-gp) :<C-u>call <SID>put('gp')<CR>
vnoremap <silent> <Plug>(tmux-clipboard-gP) :<C-u>call <SID>put('gP')<CR>
vnoremap <silent> <Plug>(tmux-clipboard-]p) :<C-u>call <SID>put(']p')<CR>
vnoremap <silent> <Plug>(tmux-clipboard-]P) :<C-u>call <SID>put(']P')<CR>
vnoremap <silent> <Plug>(tmux-clipboard-[p) :<C-u>call <SID>put('[p')<CR>
vnoremap <silent> <Plug>(tmux-clipboard-[P) :<C-u>call <SID>put('[P')<CR>

nmap p   <Plug>(tmux-clipboard-p)
nmap P   <Plug>(tmux-clipboard-P)
nmap gp  <Plug>(tmux-clipboard-gp)
nmap gP  <Plug>(tmux-clipboard-gP)
nmap ]p  <Plug>(tmux-clipboard-]p)
nmap ]P  <Plug>(tmux-clipboard-]P)
nmap [p  <Plug>(tmux-clipboard-[p)
nmap [P  <Plug>(tmux-clipboard-[P)

vmap p   <Plug>(tmux-clipboard-p)
vmap P   <Plug>(tmux-clipboard-P)
vmap gp  <Plug>(tmux-clipboard-gp)
vmap gP  <Plug>(tmux-clipboard-gP)
vmap ]p  <Plug>(tmux-clipboard-]p)
vmap ]P  <Plug>(tmux-clipboard-]P)
vmap [p  <Plug>(tmux-clipboard-[p)
vmap [P  <Plug>(tmux-clipboard-[P)

