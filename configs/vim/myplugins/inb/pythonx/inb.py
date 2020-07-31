import re
import sys
import multiprocessing
import subprocess

try:
    pyexe
except:
    pyexe = subprocess.getoutput('which python')
    sys.executable = pyexe
    multiprocessing.set_executable(pyexe)
    multiprocessing.set_start_method('spawn')

import vim
import base64
import html
import jupyter_client
import re

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
clean_ansi = lambda x: ansi_escape.sub('', x)

class inb:

    @classmethod
    def get_instance(cls):
        try:
            i = cls.instance
        except AttributeError:
            i = cls.instance = cls()
        return i

    @classmethod
    def cleanup(cls):
        try:
            i = cls.instance
        except AttributeError:
            return
        else:
            i.close_all_clients()

    def __init__(self):
        self.clients = {}

    def run_cell(self):
        win = vim.current.window
        buf = win.buffer
        block_type, code, start, end, out_end = self.get_current_block()
        kernel_name = self.get_kernel_name(block_type)
        next_pos = out_end
        if kernel_name is None:
            if block_type not in [ "md", "out" ]:
                vim.command("Error: cell language not supported")
        else:
            result_text,result_html = self.execute_cell(kernel_name, code)
            result = b""
            if result_html:
                #result_html = html.escape(result_html)
                result_html = result_html.encode("utf-8")
                #result_html = b"<pre>" + result_html + b"</pre>"
                result += result_html
            if result_text:
                result_text = html.escape(result_text)
                result_text = result_text.encode("utf-8")
                result_text = b"<pre>" + result_text + b"</pre>"
                result += result_text
            if result:
                buf[end:out_end] = [
                    b"%% out "
                    + base64.b64encode(result)
                ]
                next_pos = end+1
            else:
                buf[end:out_end] = []
                next_pos = end
        vim.command("w")
        vim.command(f":{next_pos+1}")


    def get_kernel_name(self, block_type):
        if block_type in [ 'py', 'py3', 'python3' ]:
            return 'python3'
        elif block_type in [ 'sage', 'sagemath', 'sg' ]:
            return 'sagemath'
        elif block_type in [ 'sing', 'singular' ]:
            return 'sjk-singular'
        elif block_type in [ 'm2', 'macaulay2' ]:
            return 'sjk-macaulay2'
        elif block_type in [ 'gap' ]:
            return 'sjk-gap'
        else:
            return None

    def get_current_block(self):
        win = vim.current.window
        buf = win.buffer
        num_lines = len(win.buffer)
        curr_line_num = win.cursor[0]-1
        code = []
        start = curr_line_num
        block_type = 'md'
        while True:
            line = buf[start]
            if line.startswith('%%'):
                words = line.split()
                if len(words) > 1:
                    block_type = words[1]
                break
            code.insert(0, line)
            if start > 0:
                start -= 1
            else:
                break
        end = curr_line_num + 1
        while end < num_lines:
            line = buf[end]
            if line.startswith('%%'):
                break
            code.append(line)
            end += 1
        code = "\n".join(code)
        out_end = end
        out_header_processed = False
        while out_end < num_lines:
            line = buf[out_end]
            if line.startswith('%%'):
                if out_header_processed:
                    break
                else:
                    out_header_processed = True
                    words = line.split()
                    if len(words) <= 1 or words[1] != 'out':
                        break
            out_end += 1
        return (block_type, code, start, end, out_end)

    def get_client(self, kernel_name, **kernel_args):
        if kernel_name not in self.clients:
            vim.command(f'echo "Starting kernel: {kernel_name}"')
            km = jupyter_client.KernelManager(kernel_name=kernel_name)
            km.start_kernel(**kernel_args)
            kc =  km.client()
            kc.start_channels()
            try:
                kc.wait_for_ready(timeout=60)
            except RuntimeError:
                kc.stop_channels()
                km.shutdown_kernel()
                raise
            self.clients[kernel_name] = (km, kc)
        return self.clients[kernel_name][1]

    def close_client(self, kernel_name):
        try:
            km, kc = self.clients[kernel_name]
        except:
            return
        else:
            kc.stop_channels()
            km.shutdown_kernel()
            del self.clients[kernel_name]

    def close_all_clients(self):
        for kernel_name in list(self.clients.keys()):
            self.close_client(kernel_name)

    def execute_cell(self, kernel_name, code):
        c = self.get_client(kernel_name)
        c.execute(code)
        result_text, result_html = '',''
        while True:
            try:
                msg = c.get_iopub_msg(timeout=2)
            except:
                txt  = "Waiting for cell run to finish. "
                txt += "Check again? [Y/n]: "
                vim.command(f"silent !echo [get_iopub_msg timeout]")
                vim.command('call inputsave()')
                vim.command(f"let user_input = input('{txt}')")
                vim.command('call inputrestore()')
                vim.command('redraw!')
                if vim.eval('user_input') in {"N", "n", "q", "Q"}:
                    break
                else:
                    continue
            msg = JupyterMessage(msg)
            if msg.is_idle:
                break
            t,h = msg.content
            result_text += t
            result_html += h
        return result_text, result_html


class JupyterMessage:

    def __init__(self, msg):
        self.msg = msg

    @property
    def is_idle(self):
        try:
            return self.msg['content']['execution_state'] == 'idle'
        except:
            return False

    @property
    def content(self):
        result_text = ""
        result_html = ""
        try:
            content = self.msg['content']
        except:
            pass
        else:
            if 'text' in content:
                result_text += content['text']
            if 'data' in content:
                data = content['data']
                rich = False
                if 'image/png' in data:
                    b = data['image/png']
                    result_html += f'<img src="data:image/png;base64,{b}">'
                    rich = True
                if 'text/html' in data:
                    result_html += proc_mathjax(data['text/html'])
                    rich = True
                if not rich and 'text/plain' in data:
                    result_text += data['text/plain']
            if 'traceback' in content:
                for tb in content['traceback']:
                    tb = clean_ansi(tb)
                    if not tb.endswith("\n"):
                        tb += "\n"
                    result_text += tb
        return result_text, result_html


sage_mathjax = re.compile(r"""
    \s*
    <html>\s*
    <script \s+ type="math/tex; \s+ mode=display">
    \s*
    (.*)
    \s*
    </script>
    \s*
    </html>
    \s*
""", re.MULTILINE | re.VERBOSE | re.DOTALL)

def proc_mathjax(html):
    m = sage_mathjax.match(html)
    if not m:
        return html
    else:
        return r"<blockquote>\(" + m[1] + r"\)</blockquote>"

class SignManager:

    @classmethod
    def get_instance(cls):
        try:
            i = cls.instance
        except AttributeError:
            i = cls.instance = cls()
        return i

    def __init__(self):
        self.last_sign_id = 0

    def update_signs(self):
        win = vim.current.window
        buf = win.buffer
        needed_cell_signs = set()
        needed_out_signs = set()
        for n,line in enumerate(buf):
            if line.startswith("%% out") or line.startswith("%%- out"):
                needed_out_signs.add(n+1)
            elif line.startswith("%%"):
                needed_cell_signs.add(n+1)
        current_signs = vim.eval('sign_getplaced(bufname())')[0]['signs']
        for s in current_signs:
            n = s['lnum']
            is_out = (s['name'] == 'inbOutputCellHead')

            if is_out and (n in needed_out_signs):
                needed_out_signs.remove(n)
            elif (not is_out) and (n in needed_cell_signs):
                needed_cell_signs.remove(n)
            else:
                sid = s['id']
                vim.command(f'sign unplace {sid}')
        for n in needed_out_signs:
            sid = self.last_sign_id = self.last_sign_id + 1
            vim.command(f'sign place {sid} name=inbOutputCellHead line={n}')
        for n in needed_cell_signs:
            sid = self.last_sign_id = self.last_sign_id + 1
            vim.command(f'sign place {sid} name=inbCellHead line={n}')


def run_cell():
    return inb.get_instance().run_cell()

def cleanup():
    return inb.cleanup()

def update_signs():
    return SignManager.get_instance().update_signs()
