" vi: nowrap textwidth=0

setlocal spell
set autochdir

"---------------------------------------------------------------------------------------------------
"-                                                                                                 -
"-  Folding                                                                                        -
"-                                                                                                 -
"---------------------------------------------------------------------------------------------------

function! MyManualFold()
  normal zE
  let pat = "\\(^\\s*[%\\\\]\\(section\\|chapter\\|part\\)\\W\\|^%% .*%%%\\|^%:.*\\)"
  let sec_line = search(pat, "cWn")
  while 1
    if (sec_line == 0)
      break
    elseif (sec_line == line('$'))
      break
    else
      call setpos('.',[0,sec_line+1,1,0])
    endif
    if (match(getline("."),'^\s*$') != -1)
      normal j
    endif
    let next_sec_line = search(pat, "cWn")
    if (next_sec_line == 0)
      normal VGzf
      break
    elseif (next_sec_line > line(".") + 1)
      normal V
      call setpos('.',[0,next_sec_line-1,1,0])
      if (match(getline("."),'^\s*$') != -1)
        normal k
      endif
      normal zf
    endif
    let sec_line = next_sec_line
  endwhile
  normal gg
endfunction

set foldmethod=manual
setlocal foldtext=
    \matchstr('\ \ \ \ \ \ \ \ \ \ \ \ \ ','\ \\{,'.indent(v:foldstart).'}').
    \'\ ►\ ('.(1+v:foldend-v:foldstart).'\ lines)'

call MyManualFold()

nnoremap <buffer> <leader>f :0<cr>:call MyManualFold()<cr>

"---------------------------------------------------------------------------------------------------
"-                                                                                                 -
"-  mappings                                                                                       -
"-                                                                                                 -
"---------------------------------------------------------------------------------------------------

" imap α \alpha
" imap σ \sigma
" imap δ \delta
" imap φ \phi
" imap γ \gamma
" imap η \eta
" imap ξ \xi
" imap κ \kappa
" imap λ \lambda
" imap ζ \zeta
" imap χ \chi
" imap ψ \psi
" imap ω \omega
" imap β \beta
" imap ν \nu
" imap μ \mu
" imap ε \varepsilon
" imap ρ \rho
" imap τ \tau
" imap υ \upsilon
" imap θ \theta
" imap ι \iota
" imap ο o
" imap π \pi
" 
" imap Α A
" imap Σ \Sigma
" imap Δ \Delta
" imap Φ \Phi
" imap Γ \Gamma
" imap Η \Eta
" imap Ξ \Xi
" imap Κ K
" imap Λ \Lambda
" imap Ζ Z
" imap Χ X
" imap Ψ \Psi
" imap Ω \Omega
" imap Β B
" imap Ν N
" imap Μ M
" imap Ε E
" imap Ρ P
" imap Τ T
" imap Υ Y
" imap Θ \Theta
" imap Ι I
" imap Ο O
" imap Π \Pi

call IMAP ('`0', '\emptyset',      'tex')
call IMAP ('`1', '\left',          'tex')
call IMAP ('`2', '\right',         'tex')
call IMAP ('`3', '\Big',           'tex')
call IMAP ('`6', '\partial',       'tex')
call IMAP ('`8', '\infty',         'tex')
call IMAP ('`/', '\frac{<++>}{}',  'tex')
call IMAP ('`%', '\frac{<++>}{}',  'tex')
call IMAP ('`@', '\circ',          'tex')
call IMAP ('`\|', '\Big\|',        'tex')
call IMAP ('`=', '\equiv',         'tex')
call IMAP ('`\', '\setminus',      'tex')
call IMAP ('`.', '\cdot',          'tex')
call IMAP ('`*', '\times',         'tex')
call IMAP ('`&', '\wedge',         'tex')
call IMAP ('`-', '\bigcap',        'tex')
call IMAP ('`+', '\bigcup',        'tex')
call IMAP ('`(', '\subseteq',      'tex')
call IMAP ('`)', '\supseteq',      'tex')
call IMAP ('`<', '\leq',           'tex')
call IMAP ('`>', '\geq',           'tex')
call IMAP ('`,', '\nonumber',      'tex')
call IMAP ('`~', '\tilde{<++>}',   'tex')
call IMAP ('`^', '\hat{<++>}',     'tex')
call IMAP ('`;', '\dot{<++>}',     'tex')
call IMAP ('`_', '\bar{<++>}',     'tex')

call IMAP ('__', '_{<++>}',        'tex')
call IMAP ('^^', '^{<++>}',        'tex')
call IMAP ('....', '\dots',        'tex')

call IMAP ('FEM', '\emph{<++>}',   'tex')
call IMAP ('FFF', '\emph{<++>}',   'tex')

function! s:ProtectLetters(first, last)
  let i = a:first
  while i <= a:last
    if nr2char(i) =~ '[[:print:]]'
      call IMAP('``'.nr2char(i), '``'.nr2char(i), 'tex')
      call IMAP('\`'.nr2char(i), '\`'.nr2char(i), 'tex')
      call IMAP('"`'.nr2char(i), '"`'.nr2char(i), 'tex')
    endif
    let i = i + 1
  endwhile
endfunction
call s:ProtectLetters(32, 127)

"---------------------------------------------------------------------------------------------------
"-                                                                                                 -
"-  indent paragraphs                                                                              -
"-                                                                                                 -
"---------------------------------------------------------------------------------------------------

function! s:TeX_par()
  if (getline('.') != '')
    let par_delim = '^$\|^\s*\\end{\|^\s*\\\]\|^\s*\\begin{\|^\s*\\\[\|^\s*\\label{\|^\s*\\item\|^\s*\\subsection'
    call search(par_delim, 'bW')
    normal j
    let l = line('.')
    normal! V
    call search(par_delim, 'W')
    let lastline = getline('.')
    normal k
    if (l == line('.')) || (match(lastline, '\\\]') != -1)
      normal! 
      normal jw
    else
      normal gq
      normal j
    endif
  else
    normal w
  endif
endfun

function! s:TeX_sel_par()
  let par_delim = join(
    \ ['^$', 'end', ']', 'begin', '[', 'label', 'item', 'index', '\(sub\)*section']
    \ ,'\|^\s*\\')
  let cur_line = line('.')
  let first_line = search(par_delim, 'bcWn')
  let last_line = search(par_delim, 'cWn')
  if (first_line == cur_line || last_line == cur_line)
    call setpos('.',[0,cur_line,1,0])
    normal V
  else
    if (last_line == 0)
      let last_line = line('$') + 1
    endif
    call setpos('.',[0,first_line+1,1,0])
    normal V
    call setpos('.',[0,last_line-1,1,0])
  endif
endfun

nmap <buffer><silent> Q gqapj

omap ap :call <SID>TeX_sel_par()<CR>

"---------------------------------------------------------------------------------------------------
"-                                                                                                 -
"-  F5 - add environments                                                                          -
"-                                                                                                 -
"---------------------------------------------------------------------------------------------------

inoremap <buffer><silent> <F5> x<Esc>:call <SID>DoEnvironment()<CR>

function! s:DoEnvironment()
    normal x
    let l = getline('.')
    let env = strpart(l, 0, col('.'))
    if env =~ '^\s*$'
	call <SID>PutEnvironment(l, input('Environment? '))
    else
	normal! 0D
	call <SID>SetEnvironment(env)
    endif
endfunction

function! s:SetEnvironment(env) 
  let indent = strpart(a:env, 0, match(a:env, '\S')) 
  let env = strpart(a:env, strlen(indent))
  put! =indent . '\begin{' . env . '}'
  +put =indent . '\end{' . env . '}'
  -s/^/\=indent/
  normal $
  if env == 'array'
    -s/$/{}/
    " The "$hl" magic here places the cursor at the last character
    " and not after it as "$" would.
    normal $hl
    startinsert
  elseif env =~# '^\(theorem\|lemma\|equation\|eqnarray\|align\|multline\|gather\)$'
    put!=indent . '\label{}'
    normal! f}
    startinsert
  else
    normal $
    startinsert!
  endif
endfunction

function! s:PutEnvironment(indent, env)
  put! =a:indent . '\begin{' . a:env . '}'
  +put =a:indent . '\end{' . a:env . '}'
  normal! k$
  if a:env=='array'
    call <SID>ArgumentsForArray(input("{rlc}? "))
  elseif a:env =~# '^\(theorem\|lemma\|equation\|eqnarray\|align\|multline\|gather\)$'
    execute "normal! O\\label\<C-V>{" . input("Label? ") . "}\<Esc>j"
    startinsert!
  endif
endfunction

function! s:ArgumentsForArray(arg)
    put! = '{' . a:arg . '}'
    normal! kgJj
    startinsert!
endfunction

