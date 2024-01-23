
import re
import vim

from collections import namedtuple
from pathlib import Path

########################################################################
# compiled regex
########################################################################

MATCHERS = {
    'class' : r"""
        ^
        (?P<indent> [ \t]* )
        class
        [ \t]+
        (?P<name> [a-zA-Z0-9_]+ )
        [ \t]*
        [:\(]
    """,
    'function' : r"""
        ^
        (?P<indent> [ \t]* )
        def
        [ \t]+
        (?P<name> [a-zA-Z0-9_]+ )
        [ \t]*
        \(
    """,
    '__main__' : r"""
        ^
        (?P<indent> [ \t]* )
        if
        [ \t]+
        __name__
        [ \t]+
        ==
        [ \t]+
        "(?P<name> __main__ )"
        [ \t]*
        :
    """,
    'variable' : r"""
        ^
        (?P<indent> [ \t]* )
        (?P<name> [a-zA-Z0-9_]+ )
        [ \t]*
        =
    """,
    'section' : r"""
        ^
        (?P<indent>)
        \#
        [ \t]
        (?!(?:
            import | class | def
        ))
        (?P<name> [A-Za-z0-9@_.,:;'"!? \t]+ )
        $
    """,
    # 'subsection' : r"""
    #     ^
    #     (?P<indent> [ \t]+ )
    #     \#
    #     [ \t]
    #     (?P<name> [A-Za-z_@ \t]+ )
    #     $
    # """,
}

LineMatch = namedtuple("LineMatch", "kind name indent")

class Matcher:
    def __init__(self):
        self.matchers = {
            k : re.compile(e, re.X)
            for (k,e)
            in MATCHERS.items()
        }
    def match(self, line):
        for k, matcher in self.matchers.items():
            if m := matcher.match(line):
                return LineMatch(k, m['name'], len(m['indent']))
        return None


line_matcher = Matcher().match

########################################################################
# main class
########################################################################

StackItem = namedtuple("StackItem", "indent contains")

class PyToc():

    def toc(self):
        if not self.toc_window:
            self.create_toc_window()
        else:
            self.update_toc_window()

    main_window = None
    toc_window = None
    mapping = {}

    def create_toc_window(self):
        self.main_window = vim.current.window
        width = self.populate_toc_window()
        self.do(f"""
            vertical rightb {width+2}split {self._toc_buf_name_}
            setlocal filetype=pytoc
            setlocal noreadonly
            setlocal buftype=nofile
            setlocal bufhidden=hide
            setlocal noswapfile
            setlocal nobuflisted
            setlocal nomodifiable
            setlocal textwidth=0
            setlocal colorcolumn=""
            setlocal nolist
            setlocal winfixwidth
            setlocal nospell
            setlocal foldmethod=indent
            setlocal foldignore=
            setlocal foldlevel=2
            setlocal shiftwidth=2
            setlocal foldtext=substitute(v:folddashes,'-','\ \ ','g').'['.(v:foldend-v:foldstart+1).'\ methods]'
            autocmd WinEnter <buffer> pyx pytoc.win_enter()
            noremap <buffer> <cr> :pyx pytoc.go_to()<cr>
            noremap <buffer> <2-LeftMouse> :pyx pytoc.go_to()<cr>
        """)
        self.toc_window = vim.current.window

    def populate_toc_window(self):
        self.mapping = {}
        toc_buf = self.get_toc_buffer()
        toc_buf[:] = [Path(self.main_window.buffer.name).name]
        width = 40
        for toc_num, (line_num, s) in enumerate(self.treat_file(), start=2):
            if line_num:
                self.mapping[toc_num] = line_num
                width = max(width, len(s))
            toc_buf.append(s)
        return width

    def update_toc_window(self):
        self.main_window = vim.current.window
        self.do(f"""
            {self.toc_window.number}wincmd w
            setlocal modifiable
            {self.main_window.number}wincmd w
        """)
        self.populate_toc_window()
        self.do(f"""
            {self.toc_window.number}wincmd w
            setlocal nomodifiable
        """)

    def win_enter(self):
        if len(vim.windows) == 1:
            vim.command("q")

    def do(self, *scripts):
        for script in scripts:
            for command in script.splitlines():
                command = command.strip()
                vim.command(command)

    def go_to(self):
        if not self.main_window:
            return
        toc_num = vim.current.range.start + 1
        if toc_num not in self.mapping:
            return
        self.do(f"""
            {self.main_window.number}wincmd w
            {self.mapping[toc_num]}
            normal zz
        """)

    _toc_buffer = None
    _toc_buf_name_ = "__pytoc__"

    def get_toc_buffer(self):
        if self._toc_buffer is None:
            vim.command(f"badd {self._toc_buf_name_}")
            for buf in vim.buffers:
                if buf.name.endswith(self._toc_buf_name_):
                    self._toc_buffer = buf
                    break
        return self._toc_buffer

    def treat_file(self):
        stack = [ StackItem(-1, True) ]
        prev_suffix = ":"
        for num, line in enumerate(vim.current.buffer, start=1):
            if not (m := line_matcher(line)):
                continue
            while m.indent <= stack[-1].indent:
                stack.pop()
            if not stack[-1].contains:
                continue
            name = m.name
            if m.kind == "class":
                name += ':'
                suffix = ":"
                stack.append(StackItem(m.indent, True))
            elif m.kind in ("function", "__main__"):
                name += '()'
                suffix = ":"
                stack.append(StackItem(m.indent, False))
            elif m.kind == "section":
                suffix = ":"
            elif m.kind == "subsection":
                name = f"[{name}]"
            else:
                suffix = ""
            if m.indent != 0:
                space = " " * ((m.indent+4)//2)
                suffix = ""
            else:
                if suffix or prev_suffix:
                    yield (None, "")
                if m.kind == "section":
                    space = ""
                    yield (None, "=" * 42)
                else:
                    space = "  "
                prev_suffix = suffix
            yield (num, f'{space}{name}')

########################################################################
# calling interface
########################################################################

pytoc = PyToc()
