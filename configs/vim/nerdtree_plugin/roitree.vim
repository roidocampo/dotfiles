
call NERDTreeAddKeyMap({
      \ 'key': '<left>',
      \ 'callback': 'RNTCloseDir',
      \ 'quickhelpText': 'echo full path of current node',
      \ 'scope': 'DirNode' })

call NERDTreeAddKeyMap({
      \ 'key': '<right>',
      \ 'callback': 'RNTOpenDir',
      \ 'quickhelpText': 'echo full path of current node',
      \ 'scope': 'DirNode' })

call NERDTreeAddKeyMap({
      \ 'key': '<right>',
      \ 'callback': 'RNTViewFile',
      \ 'quickhelpText': 'echo full path of current node',
      \ 'scope': 'FileNode' })

function! RNTCloseDir(dirnode)
    if a:dirnode.isRoot()
        return
    endif
    call a:dirnode.close()
    call a:dirnode.getNerdtree().render()
    call a:dirnode.putCursorHere(0, 0)
endfunction

function! RNTOpenDir(dirnode)
    call a:dirnode.open()
    call a:dirnode.getNerdtree().render()
    call a:dirnode.putCursorHere(0, 0)
endfunction

function! RNTViewFile(node)
    call a:node.open({
            \ 'reuse': 'all',
            \ "where": "p",
            \ "keepopen": 1,
        \ })
endfunction
