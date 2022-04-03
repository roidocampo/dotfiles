pythonx import vim
pythonx import tmux_send_keys

function! tmux_send_keys#SendLine() abort
    pythonx tmux_send_keys.send_line()
endfunction

function! tmux_send_keys#SendBlock() abort
    pythonx tmux_send_keys.send_block()
endfunction

function! tmux_send_keys#UpdateBlock() abort
    pythonx tmux_send_keys.send_block(False, True)
endfunction

command! -buffer -nargs=0 TskSendLine call tmux_send_keys#SendLine()
command! -buffer -nargs=0 TskSendBlock call tmux_send_keys#SendBlock()
command! -buffer -nargs=0 TskUpdateBlock call tmux_send_keys#UpdateBlock()

nnoremap <buffer> <silent> <localleader><localleader> :TskSendLine<CR>
nnoremap <buffer> <silent> <localleader>] :TskSendBlock<CR>
nnoremap <buffer> <silent> <localleader>[ :TskUpdateBlock<CR>
