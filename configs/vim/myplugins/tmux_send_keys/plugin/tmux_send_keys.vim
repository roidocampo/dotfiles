pythonx import vim
pythonx import tmux_send_keys

function! tmux_send_keys#SendLine() abort
    pythonx tmux_send_keys.send_line()
endfunction

function! tmux_send_keys#SendBlock() abort
    pythonx tmux_send_keys.send_block()
endfunction

command! -buffer -nargs=0 TskSendLine call tmux_send_keys#SendLine()
command! -buffer -nargs=0 TskSendBlock call tmux_send_keys#SendBlock()

nnoremap <buffer> <silent> <localleader><localleader> :TskSendLine<CR>
nnoremap <buffer> <silent> <localleader>] :TskSendBlock<CR>
