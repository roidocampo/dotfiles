""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Change iskeyword
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

"set iskeyword=@

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Original Colors
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" highlight Normal ctermfg=247

" highlight SpellBad ctermfg=9 cterm=NONE
" highlight SpellCap ctermfg=4 cterm=NONE
" highlight SpellRare ctermfg=4 cterm=NONE
" highlight SpellLocal ctermfg=202 cterm=NONE

" highlight C_GRAY ctermfg=242
" highlight C_GREEN ctermfg=35
" highlight C_PINK ctermfg=131
" highlight C_PURPLE ctermfg=96
" highlight C_ORANGE ctermfg=130
" highlight C_BLUE ctermfg=4
" highlight C_YELLOW ctermfg=3
" highlight C_YELLOW_GREEN ctermfg=2

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Colors
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

"highlight Normal ctermfg=20

" highlight SpellBad ctermfg=9 ctermbg=NONE cterm=NONE
" " highlight SpellBad ctermfg=9 ctermbg=NONE cterm=undercurl
" highlight SpellCap ctermfg=4 ctermbg=NONE cterm=NONE
" highlight SpellRare ctermfg=4 ctermbg=NONE cterm=NONE
" highlight SpellLocal ctermfg=202 ctermbg=NONE cterm=NONE

highlight C_GRAY ctermfg=8
highlight C_GREEN ctermfg=2
highlight C_PINK ctermfg=16
highlight C_PURPLE ctermfg=17
highlight C_ORANGE ctermfg=13
highlight C_BLUE ctermfg=4
highlight C_YELLOW ctermfg=3
highlight C_YELLOW_GREEN ctermfg=2

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Top level cluster
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syntax cluster TopLevel contains=Noop

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Matching Brackets
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syntax region ArgumentGroup 
    \ matchgroup=C_GRAY
    \ start="{" skip="\\{\|\\}" end="}" 
    \ contains=@NoSpell,@Groups contained
syntax region OptionGroup 
    \ matchgroup=C_GRAY
    \ start="\[" end="\]" 
    \ contains=@NoSpell,@Groups,Command contained
    \ nextgroup=@Groups skipwhite
syntax cluster Groups
    \ contains=ArgumentGroup,OptionGroup

highlight link ArgumentGroup C_PURPLE
highlight link OptionGroup C_ORANGE

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Comments
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syntax match ShortComment 
    \ "%.*$" 
    \ contains=@NoSpell
syntax match LongComment
    \ "%%.*$"
syntax match LongComment
    \ "%:.*$"
syntax match JinjaComment
    \ "%#.*$"
    \ contains=@NoSpell
syntax cluster Comments 
    \ contains=ShortComment,LongComment,JinjaComment

syntax cluster TopLevel add=@Comments

highlight link ShortComment C_GRAY
highlight link LongComment C_GREEN
highlight link JinjaComment C_BLUE

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Prevent spell-check
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syntax match URL 
    \ "\(http\|https\|ftp\|mailto\):\S*" 
    \ contains=@NoSpell
syntax match SingleLetter 
    \ "\<\a\>"
    \ contains=@NoSpell
syntax match TeXUnit
    \ "\d\+\(pt\|pc\|bp\|in\|cm\|mm\|dd\)"
    \ contains=@NoSpell

syntax cluster TopLevel add=URL,SingleLetter,TeXUnit

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Commands
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syntax match Command 
    \ "\\\S\(\a\|@\)*" 
    \ contains=@NoSpell
syntax match Command 
    \ "\\$" 
    \ contains=@NoSpell

let s:cmds = '"\\\('
let s:cmds.= 'documentclass'
let s:cmds.= '\|use\a*'
let s:cmds.= '\|theoremstyle'
let s:cmds.= '\|bibliography'
let s:cmds.= '\|bibliographystyle'
let s:cmds.= '\|addbibresource'
let s:cmds.= '\|printbibliography'
let s:cmds.= '\|numberwithin'
let s:cmds.= '\|setcounter'
let s:cmds.= '\|setlength'
let s:cmds.= '\|setsecnumdepth'
let s:cmds.= '\|parbox'
let s:cmds.= '\|item'
let s:cmds.= '\|cite'
let s:cmds.= '\|index'
let s:cmds.= '\|texttt'
let s:cmds.= '\|textcolor'
let s:cmds.= '\|input'
let s:cmds.= '\|include\a*'
let s:cmds.= '\|include'
let s:cmds.= '\|\a*ref\>'
let s:cmds.= '\|label'
let s:cmds.= '\|email'
let s:cmds.= '\|url'
let s:cmds.= '\|urladdr'
let s:cmds.= '\|\(this\)\=pagestyle'
let s:cmds.= '\|chapterstyle'
let s:cmds.= '\|NeedsTeXFormat'
let s:cmds.= '\|ProvidesPackage'
let s:cmds.= '\|CharacterTable'
let s:cmds.= '\|CheckSum'
let s:cmds.= '\|changes'
let s:cmds.= '\|GetFileInfo'
let s:cmds.= '\|DescribeMacro'
let s:cmds.= '\|DescribeEnv'
let s:cmds.= '\|color'
let s:cmds.= '\|pgf\a*'
let s:cmds.= '\)"'

execute "syntax match CommandWithArgs"
    \ s:cmds
    \ "contains=@NoSpell"
    \ "nextgroup=@Groups skipwhite"

syntax cluster TopLevel add=Command,CommandWithArgs

highlight link Command C_PINK
highlight link CommandWithArgs C_PINK

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Definitions
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syntax region DefinitionArgumentGroup 
    \ matchgroup=C_GRAY
    \ start="{" skip="\\{\|\\}" end="}" 
    \ contains=@NoSpell,DefinitionArgumentGroup,@TopLevel
    \ contained
syntax region DefinitionOptionGroup 
    \ matchgroup=C_GRAY
    \ start="\[" end="\]" 
    \ contains=@NoSpell,@DefinitionGroups contained
    \ nextgroup=@DefinitionGroups skipwhite
syntax match DefinitionColorModel
    \ "\c{\(named\|rgb\|cmyk\|hsb\|gray\|cmy\|HTML\|Hsb\|tHsb\)}"
    \ contains=@NoSpell,TeXDelim contained
    \ nextgroup=@DefinitionGroups skipwhite
syntax cluster DefinitionGroups 
    \ contains=DefinitionColorModel,DefinitionArgumentGroup,DefinitionOptionGroup
syntax match Definition 
    \ "\\\(\(re\)\?new\w*\|\w\?\(def\|let\)\w*\|colorlet\|set\w*\|DeclareMathOperator\)\>\*\?" 
    \ contains=@NoSpell 
    \ nextgroup=DefinedCommand,DefinedCommandGroup,DefiniedOptionGroup skipwhite
syntax match DefinedCommand
    \ "\\[^][{}]*"
    \ contains=@NoSpell contained
    \ nextgroup=@DefinitionGroups skipwhite
syntax match DefinedOption
    \ "[^][{}\\]\+"
    \ contains=@NoSpell contained
    \ nextgroup=@DefinitionGroups skipwhite
syntax match DefinedCommandGroup
    \ "{[^][{}]*}"
    \ contains=@NoSpell,DefinedCommand,DefinedOption contained
    \ nextgroup=@DefinitionGroups skipwhite
syntax region DefiniedOptionGroup 
    \ matchgroup=C_GRAY
    \ start="\[" end="\]" 
    \ contains=@NoSpell,@DefinitionGroups contained
    \ nextgroup=DefiniedOptionGroup,DefinedCommand,DefinedCommandGroup skipwhite
syntax region DefiniedOptionGroup
    \ matchgroup=C_GRAY
    \ start="(" end=")" 
    \ contains=@NoSpell,@DefinitionGroups contained
    \ nextgroup=DefiniedOptionGroup,DefinedCommand,DefinedCommandGroup skipwhite
syntax match DefinitionParam
    \ "\#\+\d*"

syntax cluster TopLevel add=Definition,DefinitionParam

highlight link Definition C_YELLOW_GREEN
highlight link DefinedCommand C_BLUE
highlight link DefinedCommandGroup C_GRAY
highlight link DefinitionOptionGroup C_PURPLE
highlight link DefinitionParam C_PURPLE

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Sections
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syntax region SectionArgumentGroup 
    \ matchgroup=C_GRAY
    \ start="{" skip="\\{\|\\}" end="}" 
    \ contains=SectionArgumentGroup,Command
    \ contained
syntax match Section
    \ "\s*\(\\\|%\)\(sub\)*\(part\|chapter\|section\|paragraph\)\>\*\?"
    \ contains=@NoSpell,SectionStar
    \ nextgroup=SectionArgumentGroup skipwhite
syntax match SectionStar
    \ "\*" 
    \ contained

syntax cluster TopLevel add=Section

highlight link Section C_GREEN
highlight link SectionStar C_GRAY
highlight link SectionArgumentGroup C_GREEN

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Begin/End
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syntax match BeginEnd 
    \ "\\\(begin\|end\)\s*{.\{-}}"
    \ contains=@NoSpell,TeXDelim,BeginEndCommand
    \ nextgroup=@Groups skipwhite
syntax match BeginEndCommand 
    \ "\\\(begin\|end\)" 
    \ contains=@NoSpell contained

syntax cluster TopLevel add=BeginEnd

highlight link BeginEnd C_PURPLE
highlight link BeginEndCommand C_GRAY

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Special Chars
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syntax match TeXSpecial "\(\\(\|\\)\|\\{\|\\}\|\\[,.;!]\)"
syntax match TeXSpecial "\(&\|\\\\\|\~\|\\\s\)"
syntax match TeXSpecial "\\\\\[[^\[\]]*\]" contains=@NoSpell
syntax match TeXSpecial "\(_\|\^\)"
syntax match TeXSpecial "\\qq*uad" contains=@NoSpell
syntax match TeXMath "\(\\\[\|\\\]\|\$\)"
syntax match TeXDelim "\({\|}\)"

syntax cluster TopLevel add=TeXSpecial,TeXMath

highlight link TeXSpecial C_GRAY
highlight link TeXMath C_PURPLE
highlight link TeXDelim C_GRAY

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" AMSRefs
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

syn match Bib 
    \ "\\bib\>" 
    \ nextgroup=BibKey
syn region BibKey
    \ matchgroup=C_GRAY
    \ start="{" end="}"
    \ contains=@NoSpell contained
    \ nextgroup=BibType
syn region BibType
    \ matchgroup=C_GRAY
    \ start="{" end="}"
    \ contains=@NoSpell contained
    \ nextgroup=BibContent
syn region BibContent
    \ matchgroup=C_GRAY
    \ start="{" end="}"
    \ contains=@Comments,BibData,@NoSpell,BibEq,BibField
    \ contained
syn match BibEq 
    \ "[=,]" 
    \ contained
syn match BibField
    \ "^\s*\zs\w\+"
    \ contains=@NoSpell contained
syn region BibData
    \ matchgroup=C_GRAY
    \ start="{" end="}"
    \ contains=BibData,@NoSpell,@Comments
    \ contained

syntax cluster TopLevel add=Bib

highlight link Bib C_GRAY
highlight link BibEq C_GRAY
highlight link BibField C_YELLOW
highlight link BibKey C_BLUE
highlight link BibType C_PURPLE
highlight link BibData C_ORANGE

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Special type of TeX files
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

let s:extfname=expand("%:e")

" if s:extfname == "sty" || s:extfname == "cls" || s:extfname == "clo" 
"    \ || s:extfname == "dtx" || s:extfname == "ltx"

if s:extfname == "dtx"

    syntax match FakeComment 
        \ "^%" 
        \ nextgroup=splitTarget
    syntax match splitTarget 
        \ "<.*>" 
        \ contains=@NoSpell contained
    syntax region Code 
        \ start="^[^%]" end="^\ze%" 
        \ contains=@NoSpell
    syntax region ShortCode 
        \ matchgroup=C_GRAY 
        \ start="|" end="|" 
        \ contains=@NoSpell
    syntax cluster Comments 
        \ add=FakeComment

    highlight link FakeComment C_GRAY
    highlight link Code C_GRAY
    highlight link splitTarget C_GREEN

endif

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" Conceal
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" Disabled for now. To enable, uncomment the lines below
" set cole=2
" set cocu=nc

highlight Conceal ctermfg=247
highlight link texMathSymbol C_PINK
highlight link texGreek C_PINK
highlight link texSuperscript C_PINK
highlight link texSubscript C_PINK
highlight link texAccent C_PINK
highlight link texLigature C_PINK

if !exists("g:tex_conceal")
 let s:tex_conceal= 'abdmgsS'
else
 let s:tex_conceal= g:tex_conceal
endif

let s:extfname=expand("%:e")
if exists("g:tex_stylish")
 let b:tex_stylish= g:tex_stylish
elseif !exists("b:tex_stylish")
 if s:extfname == "sty" || s:extfname == "cls" || s:extfname == "clo" || s:extfname == "dtx" || s:extfname == "ltx"
  let b:tex_stylish= 1
 else
  let b:tex_stylish= 0
 endif
endif

" Conceal mode support (supports set cole=2) {{{1
if has("conceal") && &enc == 'utf-8'

 " Math Symbols {{{2
 " (many of these symbols were contributed by Björn Winckler)
 if s:tex_conceal =~ 'm'
  let s:texMathList=[
    \ ['|'		, '‖'],
    \ ['aleph'		, 'ℵ'],
    \ ['amalg'		, '∐'],
    \ ['angle'		, '∠'],
    \ ['approx'		, '≈'],
    \ ['ast'		, '∗'],
    \ ['asymp'		, '≍'],
    \ ['backepsilon'	, '∍'],
    \ ['backsimeq'	, '≃'],
    \ ['backslash'	, '∖'],
    \ ['barwedge'	, '⊼'],
    \ ['because'	, '∵'],
    \ ['between'	, '≬'],
    \ ['bigcap'		, '∩'],
    \ ['bigcirc'	, '○'],
    \ ['bigcup'		, '∪'],
    \ ['bigodot'	, '⊙'],
    \ ['bigoplus'	, '⊕'],
    \ ['bigotimes'	, '⊗'],
    \ ['bigsqcup'	, '⊔'],
    \ ['bigtriangledown', '∇'],
    \ ['bigtriangleup'	, '∆'],
    \ ['bigvee'		, '⋁'],
    \ ['bigwedge'	, '⋀'],
    \ ['blacksquare'	, '∎'],
    \ ['bot'		, '⊥'],
    \ ['bowtie'	        , '⋈'],
    \ ['boxdot'		, '⊡'],
    \ ['boxminus'	, '⊟'],
    \ ['boxplus'	, '⊞'],
    \ ['boxtimes'	, '⊠'],
    \ ['bullet'	        , '•'],
    \ ['bumpeq'		, '≏'],
    \ ['Bumpeq'		, '≎'],
    \ ['cap'		, '∩'],
    \ ['Cap'		, '⋒'],
    \ ['cdot'		, '·'],
    \ ['cdots'		, '⋯'],
    \ ['circ'		, '∘'],
    \ ['circeq'		, '≗'],
    \ ['circlearrowleft', '↺'],
    \ ['circlearrowright', '↻'],
    \ ['circledast'	, '⊛'],
    \ ['circledcirc'	, '⊚'],
    \ ['clubsuit'	, '♣'],
    \ ['complement'	, '∁'],
    \ ['cong'		, '≅'],
    \ ['coprod'		, '∐'],
    \ ['copyright'	, '©'],
    \ ['cup'		, '∪'],
    \ ['Cup'		, '⋓'],
    \ ['curlyeqprec'	, '⋞'],
    \ ['curlyeqsucc'	, '⋟'],
    \ ['curlyvee'	, '⋎'],
    \ ['curlywedge'	, '⋏'],
    \ ['dagger'	        , '†'],
    \ ['dashv'		, '⊣'],
    \ ['ddagger'	, '‡'],
    \ ['ddots'	        , '⋱'],
    \ ['diamond'	, '⋄'],
    \ ['diamondsuit'	, '♢'],
    \ ['div'		, '÷'],
    \ ['doteq'		, '≐'],
    \ ['doteqdot'	, '≑'],
    \ ['dotplus'	, '∔'],
    \ ['dots'		, '…'],
    \ ['dotsb'		, '⋯'],
    \ ['dotsc'		, '…'],
    \ ['dotsi'		, '⋯'],
    \ ['dotso'		, '…'],
    \ ['doublebarwedge'	, '⩞'],
    \ ['downarrow'	, '↓'],
    \ ['Downarrow'	, '⇓'],
    \ ['ell'		, 'ℓ'],
    \ ['emptyset'	, '∅'],
    \ ['eqcirc'		, '≖'],
    \ ['eqsim'		, '≂'],
    \ ['eqslantgtr'	, '⪖'],
    \ ['eqslantless'	, '⪕'],
    \ ['equiv'		, '≡'],
    \ ['exists'		, '∃'],
    \ ['fallingdotseq'	, '≒'],
    \ ['flat'		, '♭'],
    \ ['forall'		, '∀'],
    \ ['frown'		, '⁔'],
    \ ['ge'		, '≥'],
    \ ['geq'		, '≥'],
    \ ['geqq'		, '≧'],
    \ ['gets'		, '←'],
    \ ['gg'		, '⟫'],
    \ ['gneqq'		, '≩'],
    \ ['gtrdot'		, '⋗'],
    \ ['gtreqless'	, '⋛'],
    \ ['gtrless'	, '≷'],
    \ ['gtrsim'		, '≳'],
    \ ['hbar'		, 'ℏ'],
    \ ['heartsuit'	, '♡'],
    \ ['hookleftarrow'	, '↩'],
    \ ['hookrightarrow'	, '↪'],
    \ ['iiint'		, '∭'],
    \ ['iint'		, '∬'],
    \ ['Im'		, 'ℑ'],
    \ ['imath'		, 'ɩ'],
    \ ['in'		, '∈'],
    \ ['infty'		, '∞'],
    \ ['int'		, '∫'],
    \ ['lceil'		, '⌈'],
    \ ['ldots'		, '…'],
    \ ['le'		, '≤'],
    \ ['leadsto'	, '↝'],
    \ ['left('		, '('],
    \ ['left\['		, '['],
    \ ['left\\{'	, '{'],
    \ ['leftarrow'	, '⟵'],
    \ ['Leftarrow'	, '⟸'],
    \ ['leftarrowtail'	, '↢'],
    \ ['leftharpoondown', '↽'],
    \ ['leftharpoonup'	, '↼'],
    \ ['leftrightarrow'	, '↔'],
    \ ['Leftrightarrow'	, '⇔'],
    \ ['leftrightsquigarrow', '↭'],
    \ ['leftthreetimes'	, '⋋'],
    \ ['leq'		, '≤'],
    \ ['leq'		, '≤'],
    \ ['leqq'		, '≦'],
    \ ['lessdot'	, '⋖'],
    \ ['lesseqgtr'	, '⋚'],
    \ ['lesssim'	, '≲'],
    \ ['lfloor'		, '⌊'],
    \ ['ll'		, '≪'],
    \ ['lmoustache'     , '╭'],
    \ ['lneqq'		, '≨'],
    \ ['ltimes'		, '⋉'],
    \ ['mapsto'		, '↦'],
    \ ['measuredangle'	, '∡'],
    \ ['mid'		, '∣'],
    \ ['models'		, '╞'],
    \ ['mp'		, '∓'],
    \ ['nabla'		, '∇'],
    \ ['natural'	, '♮'],
    \ ['ncong'		, '≇'],
    \ ['ne'		, '≠'],
    \ ['nearrow'	, '↗'],
    \ ['neg'		, '¬'],
    \ ['neq'		, '≠'],
    \ ['nexists'	, '∄'],
    \ ['ngeq'		, '≱'],
    \ ['ngeqq'		, '≱'],
    \ ['ngtr'		, '≯'],
    \ ['ni'		, '∋'],
    \ ['nleftarrow'	, '↚'],
    \ ['nLeftarrow'	, '⇍'],
    \ ['nLeftrightarrow', '⇎'],
    \ ['nleq'		, '≰'],
    \ ['nleqq'		, '≰'],
    \ ['nless'		, '≮'],
    \ ['nmid'		, '∤'],
    \ ['notin'		, '∉'],
    \ ['nprec'		, '⊀'],
    \ ['nrightarrow'	, '↛'],
    \ ['nRightarrow'	, '⇏'],
    \ ['nsim'		, '≁'],
    \ ['nsucc'		, '⊁'],
    \ ['ntriangleleft'	, '⋪'],
    \ ['ntrianglelefteq', '⋬'],
    \ ['ntriangleright'	, '⋫'],
    \ ['ntrianglerighteq', '⋭'],
    \ ['nvdash'		, '⊬'],
    \ ['nvDash'		, '⊭'],
    \ ['nVdash'		, '⊮'],
    \ ['nwarrow'	, '↖'],
    \ ['odot'		, '⊙'],
    \ ['oint'		, '∮'],
    \ ['ominus'		, '⊖'],
    \ ['oplus'		, '⊕'],
    \ ['oslash'		, '⊘'],
    \ ['otimes'		, '⊗'],
    \ ['owns'		, '∋'],
    \ ['P'	        , '¶'],
    \ ['parallel'	, '║'],
    \ ['partial'	, '∂'],
    \ ['perp'		, '⊥'],
    \ ['pitchfork'	, '⋔'],
    \ ['pm'		, '±'],
    \ ['prec'		, '≺'],
    \ ['precapprox'	, '⪷'],
    \ ['preccurlyeq'	, '≼'],
    \ ['preceq'		, '⪯'],
    \ ['precnapprox'	, '⪹'],
    \ ['precneqq'	, '⪵'],
    \ ['precsim'	, '≾'],
    \ ['prime'		, '′'],
    \ ['prod'		, '∏'],
    \ ['propto'		, '∝'],
    \ ['rceil'		, '⌉'],
    \ ['Re'		, 'ℜ'],
    \ ['rfloor'		, '⌋'],
    \ ['right)'		, ')'],
    \ ['right]'		, ']'],
    \ ['right\\}'	, '}'],
    \ ['rightarrow'	, '⟶'],
    \ ['Rightarrow'	, '⟹'],
    \ ['rightarrowtail'	, '↣'],
    \ ['rightleftharpoons', '⇌'],
    \ ['rightsquigarrow', '↝'],
    \ ['rightthreetimes', '⋌'],
    \ ['risingdotseq'	, '≓'],
    \ ['rmoustache'     , '╮'],
    \ ['rtimes'		, '⋊'],
    \ ['S'	        , '§'],
    \ ['searrow'	, '↘'],
    \ ['setminus'	, '∖'],
    \ ['sharp'		, '♯'],
    \ ['sim'		, '∼'],
    \ ['simeq'		, '⋍'],
    \ ['smile'		, '‿'],
    \ ['spadesuit'	, '♠'],
    \ ['sphericalangle'	, '∢'],
    \ ['sqcap'		, '⊓'],
    \ ['sqcup'		, '⊔'],
    \ ['sqsubset'	, '⊏'],
    \ ['sqsubseteq'	, '⊑'],
    \ ['sqsupset'	, '⊐'],
    \ ['sqsupseteq'	, '⊒'],
    \ ['star'		, '✫'],
    \ ['subset'		, '⊂'],
    \ ['Subset'		, '⋐'],
    \ ['subseteq'	, '⊆'],
    \ ['subseteqq'	, '⫅'],
    \ ['subsetneq'	, '⊊'],
    \ ['subsetneqq'	, '⫋'],
    \ ['succ'		, '≻'],
    \ ['succapprox'	, '⪸'],
    \ ['succcurlyeq'	, '≽'],
    \ ['succeq'		, '⪰'],
    \ ['succnapprox'	, '⪺'],
    \ ['succneqq'	, '⪶'],
    \ ['succsim'	, '≿'],
    \ ['sum'		, '∑'],
    \ ['supset'		, '⊃'],
    \ ['Supset'		, '⋑'],
    \ ['supseteq'	, '⊇'],
    \ ['supseteqq'	, '⫆'],
    \ ['supsetneq'	, '⊋'],
    \ ['supsetneqq'	, '⫌'],
    \ ['surd'		, '√'],
    \ ['swarrow'	, '↙'],
    \ ['therefore'	, '∴'],
    \ ['times'		, '×'],
    \ ['to'		, '→'],
    \ ['top'		, '⊤'],
    \ ['triangle'	, '∆'],
    \ ['triangleleft'	, '⊲'],
    \ ['trianglelefteq'	, '⊴'],
    \ ['triangleq'	, '≜'],
    \ ['triangleright'	, '⊳'],
    \ ['trianglerighteq', '⊵'],
    \ ['twoheadleftarrow', '↞'],
    \ ['twoheadrightarrow', '↠'],
    \ ['uparrow'	, '↑'],
    \ ['Uparrow'	, '⇑'],
    \ ['updownarrow'	, '↕'],
    \ ['Updownarrow'	, '⇕'],
    \ ['varnothing'	, '∅'],
    \ ['vartriangle'	, '∆'],
    \ ['vdash'		, '⊢'],
    \ ['vDash'		, '⊨'],
    \ ['Vdash'		, '⊩'],
    \ ['vdots'		, '⋮'],
    \ ['vee'		, '∨'],
    \ ['veebar'		, '⊻'],
    \ ['Vvdash'		, '⊪'],
    \ ['wedge'		, '∧'],
    \ ['wp'		, '℘'],
    \ ['wr'		, '≀']]
"    \ ['jmath'		, 'X']
"    \ ['uminus'	, 'X']
"    \ ['uplus'		, 'X']
  for texmath in s:texMathList
   if texmath[0] =~ '\w$'
    exe "syn match texMathSymbol '\\\\".texmath[0]."\\>' contains=@NoSpell conceal cchar=".texmath[1]
   else
    exe "syn match texMathSymbol '\\\\".texmath[0]."' contains=@NoSpell conceal cchar=".texmath[1]
   endif
  endfor

  if &ambw == "double"
   syn match texMathSymbol '\\gg\>'			conceal cchar=≫
   syn match texMathSymbol '\\ll\>'			conceal cchar=≪
  else
   syn match texMathSymbol '\\gg\>'			conceal cchar=⟫
   syn match texMathSymbol '\\ll\>'			conceal cchar=⟪
  endif

  syn match texMathSymbol '\\hat{a}' conceal cchar=â
  syn match texMathSymbol '\\hat{A}' conceal cchar=Â
  syn match texMathSymbol '\\hat{c}' conceal cchar=ĉ
  syn match texMathSymbol '\\hat{C}' conceal cchar=Ĉ
  syn match texMathSymbol '\\hat{e}' conceal cchar=ê
  syn match texMathSymbol '\\hat{E}' conceal cchar=Ê
  syn match texMathSymbol '\\hat{g}' conceal cchar=ĝ
  syn match texMathSymbol '\\hat{G}' conceal cchar=Ĝ
  syn match texMathSymbol '\\hat{i}' conceal cchar=î
  syn match texMathSymbol '\\hat{I}' conceal cchar=Î
  syn match texMathSymbol '\\hat{o}' conceal cchar=ô
  syn match texMathSymbol '\\hat{O}' conceal cchar=Ô
  syn match texMathSymbol '\\hat{s}' conceal cchar=ŝ
  syn match texMathSymbol '\\hat{S}' conceal cchar=Ŝ
  syn match texMathSymbol '\\hat{u}' conceal cchar=û
  syn match texMathSymbol '\\hat{U}' conceal cchar=Û
  syn match texMathSymbol '\\hat{w}' conceal cchar=ŵ
  syn match texMathSymbol '\\hat{W}' conceal cchar=Ŵ
  syn match texMathSymbol '\\hat{y}' conceal cchar=ŷ
  syn match texMathSymbol '\\hat{Y}' conceal cchar=Ŷ
 endif

 " Greek {{{2
 if s:tex_conceal =~ 'g'
  fun! s:Greek(group,pat,cchar)
    exe 'syn match '.a:group." '".a:pat."' conceal cchar=".a:cchar
  endfun
  call s:Greek('texGreek','\\alpha\>'		,'α')
  call s:Greek('texGreek','\\beta\>'		,'β')
  call s:Greek('texGreek','\\gamma\>'		,'γ')
  call s:Greek('texGreek','\\delta\>'		,'δ')
  call s:Greek('texGreek','\\epsilon\>'		,'ϵ')
  call s:Greek('texGreek','\\varepsilon\>'	,'ε')
  call s:Greek('texGreek','\\zeta\>'		,'ζ')
  call s:Greek('texGreek','\\eta\>'		,'η')
  call s:Greek('texGreek','\\theta\>'		,'θ')
  call s:Greek('texGreek','\\vartheta\>'		,'ϑ')
  call s:Greek('texGreek','\\kappa\>'		,'κ')
  call s:Greek('texGreek','\\lambda\>'		,'λ')
  call s:Greek('texGreek','\\mu\>'		,'μ')
  call s:Greek('texGreek','\\nu\>'		,'ν')
  call s:Greek('texGreek','\\xi\>'		,'ξ')
  call s:Greek('texGreek','\\pi\>'		,'π')
  call s:Greek('texGreek','\\varpi\>'		,'ϖ')
  call s:Greek('texGreek','\\rho\>'		,'ρ')
  call s:Greek('texGreek','\\varrho\>'		,'ϱ')
  call s:Greek('texGreek','\\sigma\>'		,'σ')
  call s:Greek('texGreek','\\varsigma\>'		,'ς')
  call s:Greek('texGreek','\\tau\>'		,'τ')
  call s:Greek('texGreek','\\upsilon\>'		,'υ')
  call s:Greek('texGreek','\\phi\>'		,'φ')
  " call s:Greek('texGreek','\\varphi\>'		,'ϕ')
  call s:Greek('texGreek','\\chi\>'		,'χ')
  call s:Greek('texGreek','\\psi\>'		,'ψ')
  call s:Greek('texGreek','\\omega\>'		,'ω')
  call s:Greek('texGreek','\\Gamma\>'		,'Γ')
  call s:Greek('texGreek','\\Delta\>'		,'Δ')
  call s:Greek('texGreek','\\Theta\>'		,'Θ')
  call s:Greek('texGreek','\\Lambda\>'		,'Λ')
  call s:Greek('texGreek','\\Xi\>'		,'Χ')
  call s:Greek('texGreek','\\Pi\>'		,'Π')
  call s:Greek('texGreek','\\Sigma\>'		,'Σ')
  call s:Greek('texGreek','\\Upsilon\>'		,'Υ')
  call s:Greek('texGreek','\\Phi\>'		,'Φ')
  call s:Greek('texGreek','\\Psi\>'		,'Ψ')
  call s:Greek('texGreek','\\Omega\>'		,'Ω')
  delfun s:Greek
 endif

 " Superscripts/Subscripts {{{2
 if s:tex_conceal =~ 's'

  "if s:tex_fast =~ 's'
  if exists("g:tex_fast") && s:tex_fast =~ 's'
   syn region texSuperscript	matchgroup=Delimiter start='\^{'	skip="\\\\\|\\[{}]" end='}'	concealends contains=texSpecialChar,texSuperscripts,texStatement,texSubscript,texSuperscript,texMathMatcher
   syn region texSubscript	matchgroup=Delimiter start='_{'		skip="\\\\\|\\[{}]" end='}'	concealends contains=texSpecialChar,texSubscripts,texStatement,texSubscript,texSuperscript,texMathMatcher
  endif
  fun! s:SuperSub(group,leader,pat,cchar)
    exe 'syn match '.a:group." '".a:leader.a:pat."' conceal cchar=".a:cchar
    exe 'syn match '.a:group."s '".a:pat."' conceal cchar=".a:cchar.' nextgroup='.a:group.'s'
  endfun
  call s:SuperSub('texSuperscript','\^','0','⁰')
  call s:SuperSub('texSuperscript','\^','1','¹')
  call s:SuperSub('texSuperscript','\^','2','²')
  call s:SuperSub('texSuperscript','\^','3','³')
  call s:SuperSub('texSuperscript','\^','4','⁴')
  call s:SuperSub('texSuperscript','\^','5','⁵')
  call s:SuperSub('texSuperscript','\^','6','⁶')
  call s:SuperSub('texSuperscript','\^','7','⁷')
  call s:SuperSub('texSuperscript','\^','8','⁸')
  call s:SuperSub('texSuperscript','\^','9','⁹')
  call s:SuperSub('texSuperscript','\^','a','ᵃ')
  call s:SuperSub('texSuperscript','\^','b','ᵇ')
  call s:SuperSub('texSuperscript','\^','c','ᶜ')
  call s:SuperSub('texSuperscript','\^','d','ᵈ')
  call s:SuperSub('texSuperscript','\^','e','ᵉ')
  call s:SuperSub('texSuperscript','\^','f','ᶠ')
  call s:SuperSub('texSuperscript','\^','g','ᵍ')
  call s:SuperSub('texSuperscript','\^','h','ʰ')
  call s:SuperSub('texSuperscript','\^','i','ⁱ')
  call s:SuperSub('texSuperscript','\^','j','ʲ')
  call s:SuperSub('texSuperscript','\^','k','ᵏ')
  call s:SuperSub('texSuperscript','\^','l','ˡ')
  call s:SuperSub('texSuperscript','\^','m','ᵐ')
  call s:SuperSub('texSuperscript','\^','n','ⁿ')
  call s:SuperSub('texSuperscript','\^','o','ᵒ')
  call s:SuperSub('texSuperscript','\^','p','ᵖ')
  call s:SuperSub('texSuperscript','\^','r','ʳ')
  call s:SuperSub('texSuperscript','\^','s','ˢ')
  call s:SuperSub('texSuperscript','\^','t','ᵗ')
  call s:SuperSub('texSuperscript','\^','u','ᵘ')
  call s:SuperSub('texSuperscript','\^','v','ᵛ')
  call s:SuperSub('texSuperscript','\^','w','ʷ')
  call s:SuperSub('texSuperscript','\^','x','ˣ')
  call s:SuperSub('texSuperscript','\^','y','ʸ')
  call s:SuperSub('texSuperscript','\^','z','ᶻ')
  call s:SuperSub('texSuperscript','\^','A','ᴬ')
  call s:SuperSub('texSuperscript','\^','B','ᴮ')
  call s:SuperSub('texSuperscript','\^','D','ᴰ')
  call s:SuperSub('texSuperscript','\^','E','ᴱ')
  call s:SuperSub('texSuperscript','\^','G','ᴳ')
  call s:SuperSub('texSuperscript','\^','H','ᴴ')
  call s:SuperSub('texSuperscript','\^','I','ᴵ')
  call s:SuperSub('texSuperscript','\^','J','ᴶ')
  call s:SuperSub('texSuperscript','\^','K','ᴷ')
  call s:SuperSub('texSuperscript','\^','L','ᴸ')
  call s:SuperSub('texSuperscript','\^','M','ᴹ')
  call s:SuperSub('texSuperscript','\^','N','ᴺ')
  call s:SuperSub('texSuperscript','\^','O','ᴼ')
  call s:SuperSub('texSuperscript','\^','P','ᴾ')
  call s:SuperSub('texSuperscript','\^','R','ᴿ')
  call s:SuperSub('texSuperscript','\^','T','ᵀ')
  call s:SuperSub('texSuperscript','\^','U','ᵁ')
  call s:SuperSub('texSuperscript','\^','W','ᵂ')
  call s:SuperSub('texSuperscript','\^',',','︐')
  call s:SuperSub('texSuperscript','\^',':','︓')
  call s:SuperSub('texSuperscript','\^',';','︔')
  call s:SuperSub('texSuperscript','\^','+','⁺')
  call s:SuperSub('texSuperscript','\^','-','⁻')
  call s:SuperSub('texSuperscript','\^','<','˂')
  call s:SuperSub('texSuperscript','\^','>','˃')
  call s:SuperSub('texSuperscript','\^','/','ˊ')
  call s:SuperSub('texSuperscript','\^','(','⁽')
  call s:SuperSub('texSuperscript','\^',')','⁾')
  call s:SuperSub('texSuperscript','\^','\.','˙')
  call s:SuperSub('texSuperscript','\^','=','˭')
  call s:SuperSub('texSubscript','_','0','₀')
  call s:SuperSub('texSubscript','_','1','₁')
  call s:SuperSub('texSubscript','_','2','₂')
  call s:SuperSub('texSubscript','_','3','₃')
  call s:SuperSub('texSubscript','_','4','₄')
  call s:SuperSub('texSubscript','_','5','₅')
  call s:SuperSub('texSubscript','_','6','₆')
  call s:SuperSub('texSubscript','_','7','₇')
  call s:SuperSub('texSubscript','_','8','₈')
  call s:SuperSub('texSubscript','_','9','₉')
  call s:SuperSub('texSubscript','_','a','ₐ')
  call s:SuperSub('texSubscript','_','e','ₑ')
  call s:SuperSub('texSubscript','_','i','ᵢ')
  call s:SuperSub('texSubscript','_','o','ₒ')
  call s:SuperSub('texSubscript','_','u','ᵤ')
  call s:SuperSub('texSubscript','_',',','︐')
  call s:SuperSub('texSubscript','_','+','₊')
  call s:SuperSub('texSubscript','_','-','₋')
  call s:SuperSub('texSubscript','_','/','ˏ')
  call s:SuperSub('texSubscript','_','(','₍')
  call s:SuperSub('texSubscript','_',')','₎')
  call s:SuperSub('texSubscript','_','\.','‸')
  call s:SuperSub('texSubscript','_','r','ᵣ')
  call s:SuperSub('texSubscript','_','v','ᵥ')
  call s:SuperSub('texSubscript','_','x','ₓ')
  call s:SuperSub('texSubscript','_','\\beta\>' ,'ᵦ')
  call s:SuperSub('texSubscript','_','\\delta\>','ᵨ')
  call s:SuperSub('texSubscript','_','\\phi\>'  ,'ᵩ')
  call s:SuperSub('texSubscript','_','\\gamma\>','ᵧ')
  call s:SuperSub('texSubscript','_','\\chi\>'  ,'ᵪ')
  delfun s:SuperSub
 endif

 " Accented characters: {{{2
 if s:tex_conceal =~ 'a'
  if b:tex_stylish
   syn match texAccent		"\\[bcdvuH][^a-zA-Z@]"me=e-1
   syn match texLigature		"\\\([ijolL]\|ae\|oe\|ss\|AA\|AE\|OE\)[^a-zA-Z@]"me=e-1
  else
   fun! s:Accents(chr,...)
     let i= 1
     for accent in ["`","\\'","^",'"','\~','\.',"c","H","k","r","u","v"]
      if i > a:0
       break
      endif
      if strlen(a:{i}) == 0 || a:{i} == ' ' || a:{i} == '?'
       let i= i + 1
       continue
      endif
      if accent =~ '\a'
       exe "syn match texAccent '".'\\'.accent.'\(\s*{'.a:chr.'}\|\s\+'.a:chr.'\)'."' conceal cchar=".a:{i}
      else
       exe "syn match texAccent '".'\\'.accent.'\s*\({'.a:chr.'}\|'.a:chr.'\)'."' conceal cchar=".a:{i}
      endif
      let i= i + 1
     endfor
   endfun
   "                  \`  \'  \^  \"  \~  \.  \c  \H  \k  \r  \u  \v
   call s:Accents('a','à','á','â','ä','ã','ȧ',' ',' ','ą','å','ă','ă')
   call s:Accents('A','À','Á','Â','Ä','Ã','Ȧ',' ',' ','Ą','Å','Ă','Ă')
   call s:Accents('c',' ','ć','ĉ',' ',' ','ċ','ç',' ',' ',' ',' ','č')
   call s:Accents('C',' ','Ć','Ĉ',' ',' ','Ċ','Ç',' ',' ',' ',' ','Č')
   call s:Accents('d',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','ď')
   call s:Accents('D',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','Ď')
   call s:Accents('e','è','é','ê','ë','ẽ','ė','ȩ',' ','ę',' ','ĕ','ě')
   call s:Accents('E','È','É','Ê','Ë','Ẽ','Ė','Ȩ',' ','Ę',' ','Ĕ','Ě')
   call s:Accents('g',' ','ǵ','ĝ',' ',' ','ġ','ģ',' ',' ',' ','ğ',' ')
   call s:Accents('G',' ','Ǵ','Ĝ',' ',' ','Ġ','Ģ',' ',' ',' ','Ğ',' ')
   call s:Accents('h',' ',' ','ĥ',' ',' ',' ',' ',' ',' ',' ',' ','ȟ')
   call s:Accents('H',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','Ȟ')
   call s:Accents('i','ì','í','î','ï','ĩ','į',' ',' ',' ',' ','ĭ',' ')
   call s:Accents('I','Ì','Í','Î','Ï','Ĩ','İ',' ',' ',' ',' ','Ĭ',' ')
   call s:Accents('J',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','ǰ')
   call s:Accents('k',' ',' ',' ',' ',' ',' ','ķ',' ',' ',' ',' ',' ')
   call s:Accents('K',' ',' ',' ',' ',' ',' ','Ķ',' ',' ',' ',' ',' ')
   call s:Accents('l',' ','ĺ','ľ',' ',' ',' ','ļ',' ',' ',' ',' ','ľ')
   call s:Accents('L',' ','Ĺ','Ľ',' ',' ',' ','Ļ',' ',' ',' ',' ','Ľ')
   call s:Accents('n',' ','ń',' ',' ','ñ',' ','ņ',' ',' ',' ',' ','ň')
   call s:Accents('N',' ','Ń',' ',' ','Ñ',' ','Ņ',' ',' ',' ',' ','Ň')
   call s:Accents('o','ò','ó','ô','ö','õ','ȯ',' ','ő','ǫ',' ','ŏ',' ')
   call s:Accents('O','Ò','Ó','Ô','Ö','Õ','Ȯ',' ','Ő','Ǫ',' ','Ŏ',' ')
   call s:Accents('r',' ','ŕ',' ',' ',' ',' ','ŗ',' ',' ',' ',' ','ř')
   call s:Accents('R',' ','Ŕ',' ',' ',' ',' ','Ŗ',' ',' ',' ',' ','Ř')
   call s:Accents('s',' ','ś','ŝ',' ',' ',' ','ş',' ','ȿ',' ',' ','š')
   call s:Accents('S',' ','Ś','Ŝ',' ',' ',' ','Ş',' ',' ',' ',' ','Š')
   call s:Accents('t',' ',' ',' ',' ',' ',' ','ţ',' ',' ',' ',' ','ť')
   call s:Accents('T',' ',' ',' ',' ',' ',' ','Ţ',' ',' ',' ',' ','Ť')
   call s:Accents('u','ù','ú','û','ü','ũ',' ',' ','ű','ų','ů','ŭ','ǔ')
   call s:Accents('U','Ù','Ú','Û','Ü','Ũ',' ',' ','Ű','Ų','Ů','Ŭ','Ǔ')
   call s:Accents('w',' ',' ','ŵ',' ',' ',' ',' ',' ',' ',' ',' ',' ')
   call s:Accents('W',' ',' ','Ŵ',' ',' ',' ',' ',' ',' ',' ',' ',' ')
   call s:Accents('y','ỳ','ý','ŷ','ÿ','ỹ',' ',' ',' ',' ',' ',' ',' ')
   call s:Accents('Y','Ỳ','Ý','Ŷ','Ÿ','Ỹ',' ',' ',' ',' ',' ',' ',' ')
   call s:Accents('z',' ','ź',' ',' ',' ','ż',' ',' ',' ',' ',' ','ž')
   call s:Accents('Z',' ','Ź',' ',' ',' ','Ż',' ',' ',' ',' ',' ','Ž')
   call s:Accents('\\i','ì','í','î','ï','ĩ','į',' ',' ',' ',' ','ĭ',' ')
   "                  \`  \'  \^  \"  \~  \.  \c  \H  \k  \r  \u  \v
   delfun s:Accents
   syn match texAccent   '\\aa\>'	conceal cchar=å
   syn match texAccent   '\\AA\>'	conceal cchar=Å
   syn match texAccent	'\\o\>'		conceal cchar=ø
   syn match texAccent	'\\O\>'		conceal cchar=Ø
   syn match texLigature	'\\AE\>'	conceal cchar=Æ
   syn match texLigature	'\\ae\>'	conceal cchar=æ
   syn match texLigature	'\\oe\>'	conceal cchar=œ
   syn match texLigature	'\\OE\>'	conceal cchar=Œ
   syn match texLigature	'\\ss\>'	conceal cchar=ß
  endif
 endif
endif

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" We are done!
"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

let b:current_syntax = "tex"
