#!/usr/bin/env python

import contextlib
#import ctypes
import io
import json
import os
import qpageview
import qpageview.highlight
import qpageview.magnifier
import qpageview.rubberband
import sys
import tempfile
import webbrowser

from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import *

########################################################################
# Utils
########################################################################

#libc = ctypes.CDLL(None)
#c_stderr = ctypes.c_void_p.in_dll(libc, 'stderr')

# @contextlib.contextmanager
# def stderr_redirector(stream):
#     # The original fd stderr points to. Usually 2 on POSIX systems.
#     original_stderr_fd = sys.stderr.fileno()
# 
#     def _redirect_stderr(to_fd):
#         """Redirect stderr to the given file descriptor."""
#         # Flush the C-level buffer stderr
#         #libc.fflush(c_stderr)
#         # Flush and close sys.stderr - also closes the file descriptor (fd)
#         sys.stderr.close()
#         # Make original_stderr_fd point to the same file as to_fd
#         os.dup2(to_fd, original_stderr_fd)
#         # Create a new sys.stderr that points to the redirected fd
#         sys.stderr = io.TextIOWrapper(os.fdopen(original_stderr_fd, 'wb'))
# 
#     # Save a copy of the original stderr fd in saved_stderr_fd
#     saved_stderr_fd = os.dup(original_stderr_fd)
#     try:
#         # Create a temporary file and redirect stderr to it
#         tfile = tempfile.TemporaryFile(mode='w+') #(mode='w+b')
#         _redirect_stderr(tfile.fileno())
#         # Yield to caller, then redirect stderr back to the saved fd
#         yield
#         _redirect_stderr(saved_stderr_fd)
#         # Copy contents of temporary file to the given stream
#         tfile.flush()
#         tfile.seek(0, io.SEEK_SET)
#         if stream:
#             stream.write(tfile.read())
#     finally:
#         tfile.close()
#         os.close(saved_stderr_fd)

def _create_redirector(stream_name):

    @contextlib.contextmanager
    def _redirector(new_target = None):

        if new_target is None:
            new_target = io.StringIO()

        original_fd = getattr(sys, stream_name).fileno()
        saved_fd = os.dup(original_fd)

        def _redirect_stream(target_fd):
            getattr(sys, stream_name).close()
            os.dup2(target_fd, original_fd)
            setattr(sys, stream_name, io.TextIOWrapper(os.fdopen(original_fd, 'w')))

        try:
            tfile = tempfile.TemporaryFile(mode='w+') #(mode='w+b')
            _redirect_stream(tfile.fileno())
            yield new_target
            _redirect_stream(saved_fd)
            tfile.flush()
            tfile.seek(0, io.SEEK_SET)
            if new_target:
                new_target.write(tfile.read())
        finally:
            tfile.close()
            os.close(saved_fd)

    return _redirector

redirect_stdout = _create_redirector("stdout")
redirect_stderr = _create_redirector("stderr")

########################################################################
# PdfViewerApp
########################################################################

class PdfViewerApp(QApplication):

    @classmethod
    def run(cls):
        synctex_mode = False
        try:
            try:
                cmd = sys.argv[1]
            except:
                cmd = ""
            if cmd == "--synctex":
                line = sys.argv[2]
                col = sys.argv[3]
                tex_file = sys.argv[4]
                pdf_file = sys.argv[5]
                synctex_mode = True
        except:
            print("Error: wrong arguments")
            return
        if synctex_mode:
            cls.run_synctex(line, col, tex_file, pdf_file)
        else:
            cls.run_viewer()

    @classmethod
    def run_viewer(cls):
        app = cls()
        # if file:
        #     app.open_pdf(file)
        # app.open_pdf("/Users/roi/test/tex/hola.pdf")
        app.exec()

    @classmethod
    def run_synctex(cls, line, col, tex_file, pdf_file):
        now = datetime.now()
        ts = datetime.timestamp(now)
        msg = json.dumps([ts, line, col, tex_file, pdf_file])
        dg = bytes(msg, cls.synctex_encoding)
        udp_socket = QUdpSocket()
        udp_socket.bind(QHostAddress(QHostAddress.AnyIPv4), 0)
        udp_socket.writeDatagram(
            dg,
            QHostAddress(cls.synctex_group_address),
            cls.synctex_port,
        )

    def __init__(self):
        super().__init__(sys.argv)
        self.viewers = {}
        self.init_synctex_server()
        for file in sys.argv[1:]:
            self.open_pdf(file)

    def event(self, ev):
        if ev.type() == QEvent.FileOpen:
            self.fileOpenEvent(ev)
            return True
        else:
            return super().event(ev)

    def fileOpenEvent(self, ev):
        file_path = ev.file()
        print(ev, file_path)
        self.open_pdf(file_path)

    def open_pdf(self, file):
        file = Path(file).resolve()
        if file in self.viewers:
            viewer = self.viewers[file]
            viewer.activateWindow()
        else:
            new_viewer = PdfViewer(self, file)
            self.viewers[file] = new_viewer

    def old_open_pdf(self, file):
        key = file = Path(file).resolve()
        new_viewer = PdfViewer(self, file)
        i = 0
        while key in self.viewers:
            i += 1
            key = f"{file}_@_{i}"
        self.viewers[key] = new_viewer

    synctex_port = 45454
    synctex_group_address = "239.255.43.21"
    synctex_encoding = "utf-8"

    def init_synctex_server(self):
        self.synctex_proc = None
        self.synctex_queue = []
        self.synctex_ts = -1
        self.udp_socket = QUdpSocket(self)
        self.udp_socket.bind(QHostAddress.AnyIPv4, self.synctex_port, QUdpSocket.ShareAddress);
        self.udp_socket.joinMulticastGroup(QHostAddress(self.synctex_group_address));
        self.udp_socket.readyRead.connect(self.synctexMessageEvent)

    def synctexMessageEvent(self, *args):
        dg_size = self.udp_socket.pendingDatagramSize()
        dg, addr, ip = self.udp_socket.readDatagram(dg_size)
        msg = str(dg, self.synctex_encoding)
        try:
            ts, line, col, tex_file, pdf_file = json.loads(msg)
        except:
            return
        if ts < self.synctex_ts:
            return
        if Path(pdf_file).resolve() not in self.viewers:
            return
        self.synctex_ts = ts
        self.synctex_queue.append(("view", line, col, tex_file, pdf_file))
        self.proc_synctex_queue()

    def proc_synctex_queue(self):
        if self.synctex_proc is not None:
            return
        if not self.synctex_queue:
            return
        self.synctex_mode, *args = self.synctex_queue.pop(0)
        if self.synctex_mode == "view":
            line, col, tex_file, pdf_file = args
            cmd = f"synctex view -i {line}:{col}:{tex_file} -o {pdf_file}"
        elif self.synctex_mode == "edit":
            page_num, x, y, pdf_file = args
            cmd = f"synctex edit -o {page_num}:{x}:{y}:{pdf_file}"
        else:
            return
        self.synctex_proc = QProcess()
        self.synctex_out = ""
        self.synctex_proc.readyReadStandardOutput.connect(self.synctex_handle_output)
        self.synctex_proc.finished.connect(self.synctex_handle_finish)
        self.synctex_proc.start(cmd)

    def synctex_handle_output(self):
        data = self.synctex_proc.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.synctex_out += stdout

    def synctex_handle_finish(self):
        if self.synctex_out:
            data = {}
            for line in self.synctex_out.splitlines():
                k, v, *r = (line + ":").split(":")
                if k in data:
                    break
                if v:
                    data[k] = v
            if self.synctex_mode == "view":
                self.synctex_handle_finish_view(data)
            elif self.synctex_mode == "edit":
                self.synctex_handle_finish_edit(data)
        self.synctex_proc = None
        self.proc_synctex_queue()

    def synctex_handle_finish_view(self, data):
        try:
            pdf_file = Path(data["Output"]).resolve()
        except:
            return
        if pdf_file not in self.viewers:
            return
        viewer = self.viewers[pdf_file]
        viewer.handle_synctex_goto(data)

    def synctex_handle_finish_edit(self, data):
        try:
            tex_file = Path(data["Input"]).resolve()
            line = int(data["Line"])
            col = int(data["Column"])
        except:
            pass
        else:
            tex_file_name = str(tex_file)
            tex_file_id = tex_file_name.replace("/","_@_")
            sync_dir = Path.home() / ".skim_vim_search"
            sync_dir.mkdir(exist_ok=True)
            sync_file = sync_dir / tex_file_id
            now = datetime.now()
            ts = datetime.timestamp(now)
            with sync_file.open("w") as f:
                f.write(str(ts) + "\n" + str(line) + "\n")

########################################################################
# PdfViewer
########################################################################

class PdfViewer(
    qpageview.link.LinkViewMixin,
    qpageview.shadow.ShadowViewMixin,
    qpageview.highlight.HighlightViewMixin,
    qpageview.view.View
):

    def __init__(self, app, file):
        super().__init__()
        self.app = app
        self.file = Path(file).resolve()
        self.position_history = []
        self.init_window()
        #self.init_magnifier()
        self.init_rubberband()
        self.init_view()
        self.init_document()
        self.show()

    def init_window(self):
        self.setWindowFlags(
            Qt.CustomizeWindowHint
            #| Qt.WindowStaysOnTopHint
        )
        ag = self.app.desktop().availableGeometry()
        self.resize(ag.width(), ag.height())
        self.kineticScrollingEnabled = False
        self.setWindowTitle(f"{self.file.name} ({self.file.parent})")

    def init_magnifier(self):
        m = qpageview.magnifier.Magnifier()
        self.setMagnifier(m)

    def init_rubberband(self):
        r = qpageview.rubberband.Rubberband()
        self.setRubberband(r)

    def init_view(self):
        self.setViewMode(qpageview.FitWidth)

    def init_document(self):
        self._document_loaded = False
        self.load_document_safe()
        self.reloader_timer = QTimer()
        self.reloader_timer.timeout.connect(self.autoReloadEvent)
        self.reloader_timer.start(1000)

    def load_document_safe(self):
        with redirect_stderr() as err:
            self.loadPdf(str(self.file))
        if self.document().document():
            self._document_loaded = True
            self._document_load_error = None
            self._document_mtime = self.file.stat().st_mtime
        else:
            self._document_loaded = False
            self._document_load_error = err.getvalue()
            self._document_mtime = -1

    def autoReloadEvent(self):
        if self.file.exists():
            if self._document_loaded:
                new_mtime = self.file.stat().st_mtime
                if new_mtime > self._document_mtime:
                    self.reload()
                    self._document_mtime = new_mtime
            else:
                self.load_document_safe()
        else:
            self._document_mtime = -1
            if self._document_loaded:
                self.clear()
                self._document_loaded = False
                self._document_load_error = None

    def handle_synctex_goto(self, data):
        try:
            page_num = int(data["Page"])
            page = self.page(page_num)
            x = float(data["x"]) / page.pageWidth
            y = float(data["y"]) / page.pageHeight
            h = float(data["h"])
            v = float(data["v"])
            W = float(data["W"])
            H = float(data["H"])
            area = QRectF(
                h / page.pageWidth,
                v / page.pageHeight,
                W / page.pageWidth,
                -H / page.pageHeight,
            )
            margins = QMargins(0,150,0,150)
        except:
            pass
        else:
            self.setPosition((page_num, x, y))
            self.highlight(
                { page: [area] },
                msec = 10000,
                scroll = True,
                margins = margins,
            )

    def keyPressEvent(self, ev):
        key = ev.key()
        mod = ev.modifiers()
        if key == Qt.Key_Equal:
            self.zoomIn()
        elif key == Qt.Key_Minus:
            self.zoomOut()
        elif key == Qt.Key_0:
            #self.setZoomFactor(1.0)
            self.setViewMode(qpageview.FitWidth)
        elif key == Qt.Key_1:
            self.setPageLayoutMode("single")
        elif key == Qt.Key_2:
            self.setPageLayoutMode("double_right")
        elif key == Qt.Key_3:
            self.setPageLayoutMode("double_left")
        # elif key == Qt.Key_Q and mod == Qt.ControlModifier:
        #     self.app.quit()
        elif key == Qt.Key_R:
            print("reload!")
            self.reload()
        elif key == Qt.Key_W and mod == Qt.ControlModifier:
            self.close()
        else:
            super().keyPressEvent(ev)

    def linkClickEvent(self, ev, page, link):
        if link.url:
            webbrowser.open(link.url)
            return
        try:
            dest = link.linkobj.destination()
            p = dest.pageNumber()
            x = dest.left()
            y = dest.top()
        except:
            return
        self.setPosition(qpageview.view.Position(p,x,y))

    def mousePressEvent(self, ev):
        mod = ev.modifiers()
        if mod & (Qt.ControlModifier | Qt.ShiftModifier):
            pos_on_layout = ev.pos() - self.layoutPosition()
            page = self.pageLayout().pageAt(pos_on_layout)
            if page:
                pos_on_page = pos_on_layout - page.pos()
                pos = page.mapFromPage().point(pos_on_page)
                page_num = page.ident() + 1
                x = pos.x()
                y = pos.y()
                self.app.synctex_queue.append(("edit", page_num, x, y, str(self.file)))
                self.app.proc_synctex_queue()
                return
        super().mousePressEvent(ev)

########################################################################
# main
########################################################################

if __name__ == "__main__":
    PdfViewerApp.run()#"/Users/roi/test/old/arc-fiber-2022-1208.pdf")
