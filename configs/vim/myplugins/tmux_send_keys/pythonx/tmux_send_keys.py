from subprocess import call, check_output
import vim

target_pane = None

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

def escape_code(code):
    out = []
    for line in code:
        if line and line[-1] == ";":
            line = line[:-1] + "\;"
        out.append(line)
    return out

def send_code(code):
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
    elif line[:2] == "//":
        return True
    elif line[:2] == "--":
        return True
    else:
        return False

def send_block():
    win = vim.current.window
    buf = win.buffer
    num_lines = len(win.buffer)
    start = win.cursor[0]-1
    move = 0
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
    while code and (code[0].isspace() or not code[0]):
        code = code[1:]
    while code and (code[-1].isspace() or not code[-1]):
        code = code[:-1]
    if not code:
        vim.command("normal %sj" % move)
        return
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
