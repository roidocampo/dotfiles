from subprocess import call, check_output
import vim
import re

target_pane = None
previous_output = ""

rgx_begin_code_block = re.compile(r"""
    ^\s*
    \\begin\{
    \s*
    (?P<type>
        code
        | m2
        | macaulay2
        | sing
        | singular
        | sage
        | sagemath
        | py
        | python
    )
    \s*
    \*?
    \}
""", re.X)

rgx_end_code_block = re.compile(r"""
    ^\s*
    \\end\{
    \s*
    (
        code
        | m2
        | macaulay2
        | sing
        | singular
        | sage
        | sagemath
        | py
        | python
    )
    \s*
    \*?
    \}
    \s*
    $
""", re.X)

rgx_split = re.compile(r"""
    \ * (?: \n | \r )
""", re.X)

rgx_m2 = re.compile(r"""
    ^
    (?P<tag> i|o)
    (?P<num> \d+)
    \s+ (:|=) \s
""", re.X)

rgx_sing = re.compile(r"""
    ^
    (?P<mode> > | \. )
    \ 
""", re.X)

rgx_py = re.compile(r"""
    ^
    (?:
        > > > \ 
        |
        \. \. \. \ 
        |
        In \ \[ \d+ \] : \ 
        |
        \s* \.\.\. : \ 
    )
""", re.X)

def init_target_pane():
    global target_pane
    o1 = check_output(['tmux', 'display', '-p', '#D'])
    current_pane = o1.strip()
    call(['tmux', 'select-pane', '-R'])
    o2 = check_output(['tmux', 'display', '-p', '#D'])
    default_target_pane = o2.strip()
    call(['tmux', 'set-option', 'display-time', '0'])
    call(['tmux', 'display', 'Select target pane'])
    call([ 'tmux', 'display-panes', '-d', '0' ])
    o3 = check_output(['tmux', 'display', '-p', '#D'])
    target_pane = o3.strip()
    call(['tmux', 'select-pane', '-t', current_pane])
    call(['tmux', 'set-option', 'display-time', '1'])
    call(['tmux', 'display', ''])
    call(['tmux', 'set-option', 'display-time', '750'])
    if target_pane == b"":
        target_pane = default_target_pane
    if current_pane == target_pane:
        target_pane = None
    save_previous_output()

def escape_code(code):
    out = []
    for line in code:
        if line and line[-1] == ";":
            line = line[:-1] + "\;"
        out.append(line)
    return out

def send_code(code):
    save_previous_output()
    global target_pane
    if target_pane is None:
        init_target_pane()
    if target_pane is not None:
        call([
            'tmux',
            'send-keys',
            '-t',
            target_pane
        ] + escape_code(code))
        return True
    return False

def send_line():
    line = vim.current.line
    code = [ line, "Enter" ]
    s = send_code(code)
    if s:
        vim.command("normal j")

def is_comment_line(line):
    if not line:
        return False
    elif line[:2] == "##":
        return True
    #elif line[:2] == "//":
    #    return True
    elif line[:2] == "--":
        return True
    elif rgx_begin_code_block.match(line):
    #elif line[:1+5+1+2+1] == r"\begin{m2}":
        return True
    elif rgx_end_code_block.match(line):
    #elif line[:1+3+1+2+1] == r"\end{m2}":
        return True
    else:
        return False

def filter_code(code, filter_type):
    if filter_type in ('m2', 'macaulay2'):
        return filter_code_m2(code)
    elif filter_type in ('sing', 'singular'):
        return filter_code_sing(code)
    elif filter_type in ('py', 'python', 'sage', 'sagemath'):
        return filter_code_py(code)
    else:
        return code

def filter_code_sing(code):
    has_input_marks = False
    mode = '>'
    ind = 0
    new_code = []
    for line in code:
        m = rgx_sing.match(line)
        if m:
            has_input_marks = True
            mode = m['mode']
            ind = 2
        elif has_input_marks:
            mode = None
        if mode is not None:
            new_code.append(line[ind:].rstrip())
    while new_code and not new_code[-1]:
        del new_code[-1]
    return new_code

def filter_code_py(code):
    has_input_marks = False
    is_input_line = True
    ind = 0
    new_code = []
    for line in code:
        m = rgx_py.match(line)
        if m:
            has_input_marks = True
            ind = len(m[0])
            is_input_line = True
        elif has_input_marks:
            is_input_line = False
        if is_input_line:
            new_code.append(line[ind:].rstrip())
    while new_code and not new_code[-1]:
        del new_code[-1]
    if new_code and new_code[-1] and new_code[-1][0] == ' ':
        new_code.append("")
    return new_code

def filter_code_m2(code):
    old_tag = None
    tag = None
    ind = 0
    new_code = []
    for line in code:
        m = rgx_m2.match(line)
        if m:
            old_tag = tag
            tag = m['tag']
            ind = len(m[0])
        if tag == 'o' and old_tag == 'i':
            while new_code and new_code[-1]:
                del new_code[-1]
        elif tag in (None, 'i'):
            if m:
                while new_code and not new_code[-1]:
                    del new_code[-1]
            new_code.append(line[ind:].rstrip())
    while new_code and not new_code[-1]:
        del new_code[-1]
    return new_code

def send_block(do_send=True, do_update=False):
    win = vim.current.window
    buf = win.buffer
    num_lines = len(win.buffer)
    start = win.cursor[0]-1
    move = 0
    if do_update and start > 0:
        if rgx_end_code_block.match(buf[start]):
            #print("here", start, "=>", buf[start])
            start -= 1
    #print("after", start, "=>", buf[start])
    while start < num_lines:
        line = buf[start]
        if is_comment_line(line):
            start += 1
            move += 1
        else:
            break
    if start == num_lines:
        vim.command("normal %sj" % move)
        return
    end = start
    code = [ buf[start] ]
    code_type = None
    while start > 0:
        prev_line = buf[start-1]
        if is_comment_line(prev_line):
            break
        else:
            code.insert(0, prev_line)
            start -= 1
    while end < num_lines-1:
        next_line = buf[end+1]
        if is_comment_line(next_line):
            move += 1
            break
        else:
            code.append(next_line)
            end += 1
            move += 1
    if start > 0:
        if rgx_end_code_block.match(buf[start-1]):
            code = []
        else:
            m = rgx_begin_code_block.match(buf[start-1])
            if m:
                code_type = m['type']
    if do_send:
        code = filter_code(code, code_type)
    while code and (code[0].isspace() or not code[0]):
        code = code[1:]
    trailing_empty_lines = False
    while code and (code[-1].isspace() or not code[-1]):
        trailing_empty_lines = True
        code = code[:-1]
    if trailing_empty_lines and code_type in ('py', 'python', 'sage', 'sagemath'):
        code.append("")
    if not code:
        vim.command("normal %sj" % move)
        return
    if do_send:
        full_code = []
        for i,line in enumerate(code):
            if i:
                full_code.append('C-Q')
                full_code.append('C-J')
            full_code.append(line)
        full_code.append('Enter')
        s = send_code(full_code)
        if s:
            vim.command("normal %sj" % move)
    if do_update:
        global previous_output
        out0 = rgx_split.split(previous_output)
        while out0 and not out0[-1]:
            del out0[-1]
        out1 = rgx_split.split(get_pane_contents())
        while out1 and not out1[-1]:
            del out1[-1]
        if out1:
            del out1[-1]
        while out1 and not out1[-1]:
            del out1[-1]
        s0 = '\n'.join(out0)
        s1 = '\n'.join(out1)
        while out0 and not s1.startswith(s0):
            del out0[0]
            s0 = '\n'.join(out0)
        while out0 and out1:
            if out1[0] == out0[0]:
                del out0[0]
                del out1[0]
            else:
                break
        if not out1:
            print("no new output to update")
            return
        buf[start:end+1] = out1

def save_previous_output():
    global previous_output
    previous_output = get_pane_contents()

def get_pane_contents(pane=None):
    global target_pane
    if pane is None:
        pane = target_pane
    if pane is None:
        return None
    return check_output([
        'tmux', 
        'capture-pane', 
        '-pJS', 
        '-',
        '-t',
        pane
    ]).decode("utf-8")
