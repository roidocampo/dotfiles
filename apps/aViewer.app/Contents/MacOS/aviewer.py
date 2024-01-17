#!/usr/bin/env python

import contextlib
#import ctypes
import io
import json
import os
import qpageview
import qpageview.highlight
import qpageview.magnifier
import qpageview.poppler
import qpageview.rubberband
import qpageview.widgetoverlay
import subprocess
import sys
import tempfile
import webbrowser

from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import *
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWebEngineWidgets import *

########################################################################
# FixedPopplerRenderer
########################################################################

_old_createPages = qpageview.poppler.PopplerDocument.createPages

def _new_createPages(self):
    pages = _old_createPages(self)
    if not pages:
        return ()
    for page in pages:
        page._qpdoc = self
        yield page

qpageview.poppler.PopplerDocument.createPages = _new_createPages

class ProxyPainter:
    def __init__(self, painter):
        self.painter = painter
    def device(self, *args, **kws):
        return self.painter.device()
    def fillRect(self, *args, **kws):
        pass
    def drawImage(self, *args, **kws):
        pass

class FixedPopplerRenderer(qpageview.poppler.PopplerRenderer):

    def setRenderHints(self, doc):
        """Set the poppler render hints we want to set."""
        import popplerqt5
        if self.antialiasing:
            doc.setRenderHint(popplerqt5.Poppler.Document.Antialiasing)
            doc.setRenderHint(popplerqt5.Poppler.Document.TextAntialiasing)
            # doc.setRenderHint(popplerqt5.Poppler.Document.TextHinting)

    # def schedule(self, page, *args, **kws):
    #     print(page.pageNumber, flush=True)
    #     return super().schedule(page, *args, **kws)

    def paint(self, page, painter, rect, callback=None):
        page_num = page.pageNumber
        doc = page._qpdoc
        pages = doc.pages()
        cb = lambda *args, **kws: None
        for offset in [1, -1, 2, -2]:
            idx = page_num + offset
            if 0 <= idx < len(pages):
                neigh_page = pages[idx]
                super().paint(neigh_page, ProxyPainter(painter), rect, cb)
        super().paint(page, painter, rect, callback)


qpageview.poppler.PopplerPage.renderer = FixedPopplerRenderer()

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
                try:
                    synctex_dir = sys.argv[6]
                except:
                    synctex_dir = None
        except:
            print("Error: wrong arguments")
            return
        if synctex_mode:
            cls.run_synctex(line, col, tex_file, pdf_file, synctex_dir)
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
    def run_synctex(cls, line, col, tex_file, pdf_file, synctex_dir):
        now = datetime.now()
        ts = datetime.timestamp(now)
        msg = json.dumps([ts, line, col, tex_file, pdf_file, synctex_dir])
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
        # self.documents = {}
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
        self.open_pdf(file_path)

    def open_pdf(self, file):
        file = Path(file).resolve()
        if file in self.viewers:
            viewer = self.viewers[file]
            viewer.raise_()
            viewer.activateWindow()
        else:
            if file.suffix == ".html":
                new_viewer = HtmlViewer(self, file)
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
            ts, line, col, tex_file, pdf_file, synctex_dir = json.loads(msg)
        except:
            return
        if ts < self.synctex_ts:
            return
        if Path(pdf_file).resolve() not in self.viewers:
            self.open_pdf(pdf_file)
        self.synctex_ts = ts
        self.synctex_queue.append(("view", line, col, tex_file, pdf_file, synctex_dir))
        self.proc_synctex_queue()

    def proc_synctex_queue(self):
        if self.synctex_proc is not None:
            return
        if not self.synctex_queue:
            return
        self.synctex_mode, *args = self.synctex_queue.pop(0)
        if self.synctex_mode == "view":
            line, col, tex_file, pdf_file, synctex_dir = args
            if synctex_dir is not None:
                self.synctex_handle_set_synctex_dir(pdf_file, synctex_dir)
                cmd = f"synctex view -i {line}:{col}:{tex_file} -o {pdf_file} -d {synctex_dir}"
            else:
                cmd = f"synctex view -i {line}:{col}:{tex_file} -o {pdf_file}"
        elif self.synctex_mode == "edit":
            page_num, x, y, pdf_file, synctex_dir = args
            if synctex_dir is not None:
                cmd = f"synctex edit -o {page_num}:{x}:{y}:{pdf_file} -d {synctex_dir}"
            else:
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

    def synctex_handle_set_synctex_dir(self, pdf_file, synctex_dir):
        try:
            pdf_file = Path(pdf_file).resolve()
        except:
            return
        if pdf_file not in self.viewers:
            return
        viewer = self.viewers[pdf_file]
        viewer.synctex_dir = synctex_dir

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
# MoviePlayer
########################################################################

class MoviePlayer(QLabel):

    @classmethod
    def make(cls, view, file, page_num=1):
        obj = cls(view, file, page_num)
        return obj.movie

    def __init__(self, view, file, page_num=1):
        QLabel.__init__(self)
        # self.setStyleSheet('border: 1px solid red')
        # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setScaledContents(True)
        self.file = file
        self.movie = QMovie(str(file))
        self.setMovie(self.movie)
        self.movie.setScaledSize(self.size())
        view.addWidget(self, view.page(page_num))
        self.movie.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.movie.setScaledSize(event.size())

########################################################################
# HtmlViewer
########################################################################

class HtmlViewer(QMainWindow):

    EML_HEAD = """<!doctype html>
        <html lang="en">
        <meta charset="utf-8">
        <style>
        /*
            html {
                overflow : hidden;
                width: 100%;
                height: 100%;
                background-color: #ccc;
                text-align: center;
                box-sizing: border-box;
                padding: 0px;
                margin: 0px;
            }
            *, *:before, *:after {
                box-sizing: inherit;
            }
            body {
                overflow : hidden;
                width: 100%;
                height: 100%;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 12pt;
                text-align: center;
                padding-top: 10px;
                margin: 0px;
                position: relative;
            }
        */
            #aviewer_content {
                overflow : auto;
                background-color: white;
                text-align: left;
                max-width: 700px;
                height: calc(100% - 10px);
                margin: 0px auto;
                background-color: shite;
                padding: 20px ;
                border: 1px solid #666;
                position: relative;
            }
            .lds-dual-ring {
                position: absolute;
                display: flex;
                background-color: #000a;
                border: 1px solid black;
                top: 0px;
                bottom: 0px;
                left: 0px;
                right: 0px;
                justify-content: center;
                align-items: center;
            }
            .lds-dual-ring:after {
                content: " ";
                display: inline-block;
                width: 64px;
                height: 64px;
                border-radius: 50%;
                border: 6px solid #ccc;
                border-color: #ccc transparent #ccc transparent;
                animation: lds-dual-ring 1.2s linear infinite;
            }
            @keyframes lds-dual-ring {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(360deg);
                }
            }
        </style>
        <div id="aviewer_content">
    """

    def __init__(self, app, file, page_num=1):
        super().__init__()
        self.app = app
        self.on_top = False
        self.file = Path(file).resolve()
        self.eml_file = self.file.with_suffix(".eml")
        self.browser = QWebEngineView(self)
        self.setCentralWidget(self.browser)
        self.init_window()
        self.init_menu()
        self.init_document()
        self.show()

    def init_window(self):
        self.toggle_on_top(self.on_top, False)
        self.init_size()
        self.setWindowTitle(f"{self.file.name} ({self.file.parent})")
        self.browser.installEventFilter(self)

    def init_menu(self):
        self.menu_bar = QMenuBar(self)
        self.toc_menu = self.menu_bar.addMenu(self.file.name)
        self.toc_menu.setTitle("Loading...")
        self.toc_menu.addAction("HTML file")

    def update_menu_title(self):
        self.toc_menu.setTitle(
            f"{self.file.name} ({self.file.parent})"
        )

    def init_document(self):
        self._document_loaded = False
        self._scroll_jobs = []
        self.load_document()
        self.reloader_timer = QTimer()
        self.reloader_timer.timeout.connect(self.autoReloadEvent)
        self.reloader_timer.start(1000)

    def load_document(self):
        if self._document_loaded and not self._scroll_jobs:
            document_scroll = self.browser.page().scrollPosition()
        else:
            document_scroll = None
        if self.eml_file.exists():
            html = self.EML_HEAD
            with open(self.file, "r") as f:
                html += f.read()
            self.browser.setHtml(html)
        else:
            self.browser.load(QUrl("file://" + str(self.file)))
        self._document_loaded = True
        self._document_mtime = self.file.stat().st_mtime
        self.update_menu_title()
        if document_scroll is not None:
            self._scroll_jobs.append(document_scroll)

    def autoReloadEvent(self):
        if self._document_loaded:
            while self._scroll_jobs:
                document_scroll = self._scroll_jobs.pop(0)
                x = document_scroll.x()
                y = document_scroll.y()
                print(f"window.scrollTo({x}, {y});", flush=True)
                self.browser.page().runJavaScript(f"window.scrollTo({x}, {y});")
        if self.file.exists():
            if self._document_loaded:
                new_mtime = self.file.stat().st_mtime
                if new_mtime > self._document_mtime:
                    self.load_document()
                    # self.reload()
                    # self.populate_toc_menu()
                    self._document_mtime = new_mtime
            else:
                self.load_document()
        else:
            self._document_mtime = -1
            if self._document_loaded:
                # self.clear()
                self._document_loaded = False
                self._document_load_error = None


    def toggle_on_top(self, on_top=None, show=True):
        if on_top is None:
            self.on_top = not self.on_top
        else:
            self.on_top = on_top
        flags = Qt.CustomizeWindowHint
        if self.on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        if show:
            self.show()

    def init_size(self):
        ag = self.app.desktop().availableGeometry()
        if ag.height() > 1400:
            self.size_state = [2, 1]
            self.resize_to_right()
        else:
            self.size_state = [1, 0]
            self.resize_full()

    def resize_full(self):
        ag = self.app.desktop().availableGeometry()
        self.move(ag.left(), ag.top())
        self.resize(ag.width(), ag.height())
        self.size_state = [1, 0]

    def resize_to_left(self):
        ag = self.app.desktop().availableGeometry()
        if self.size_state == [1, 0]:
            self.move(ag.left(), ag.top())
            self.resize(ag.width()//2, ag.height())
            self.size_state = [2, 0]
        elif self.size_state == [2, 0]:
            self.move(ag.left(), ag.top())
            self.resize(8*ag.width()//19, ag.height())
            self.size_state = [2.375, 0]
        elif self.size_state == [2, 1]:
            self.move(ag.left(), ag.top())
            self.size_state = [2, 0]
        elif self.size_state == [2.375, 0]:
            self.move(ag.left(), ag.top())
            self.resize(ag.width()//3, ag.height())
            self.size_state = [3, 0]
        elif self.size_state == [2.375, 1]:
            self.move(ag.left(), ag.top())
            self.size_state = [2.375, 0]
        elif self.size_state == [3, 1]:
            self.move(ag.left(), ag.top())
            self.size_state = [3, 0]
        elif self.size_state == [3, 2]:
            self.move(ag.left()+ag.width()//3+1, ag.top())
            self.size_state = [3, 1]
        # pos = self.position()
        # self.setPosition(qpageview.view.Position(
        #     pos.pageNumber, 0.5, pos.y
        # ))

    def resize_to_right(self):
        ag = self.app.desktop().availableGeometry()
        if self.size_state == [1, 0]:
            self.move(ag.left()+ag.width()//2+1,ag.top())
            self.resize(ag.width()//2, ag.height())
            self.size_state = [2, 1]
        elif self.size_state == [2, 0]:
            self.move(ag.left()+ag.width()//2+1,ag.top())
            self.size_state = [2, 1]
        elif self.size_state == [2, 1]:
            self.move(ag.left()+11*ag.width()//19+1,ag.top())
            self.resize(8*ag.width()//19, ag.height())
            self.size_state = [2.375, 1]
        elif self.size_state == [2.375, 0]:
            self.move(ag.left()+11*ag.width()//19+1,ag.top())
            self.size_state = [2.375, 1]
        elif self.size_state == [2.375, 1]:
            self.move(ag.left()+2*ag.width()//3+1,ag.top())
            self.resize(ag.width()//3, ag.height())
            self.size_state = [3, 2]
        elif self.size_state == [3, 0]:
            self.move(ag.left()+ag.width()//3+1,ag.top())
            self.size_state = [3, 1]
        elif self.size_state == [3, 1]:
            self.move(ag.left()+2*ag.width()//3+1,ag.top())
            self.size_state = [3, 2]
        # pos = self.position()
        # self.setPosition(qpageview.view.Position(
        #     pos.pageNumber, 0.5, pos.y
        # ))

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress):
            key = ev.key()
            if ev.key in [
                Qt.Key_C,
                Qt.Key_Comma,
                Qt.Key_Period,
                Qt.Key_M,
                Qt.Key_T,
                Qt.Key_R,
                Qt.Key_W,
                Qt.Key_H,
                Qt.Key_Question,
            ]:
                return False
        return super().eventFilter(source, event)

    def clipboard_copy_html(self):
        if self.file.exists():
            with open(self.file) as f:
                html = f.read()
            cb_data = QMimeData()
            cb_data.setText(html)
            cb_data.setHtml(html)
            cb = QGuiApplication.clipboard()
            cb.setMimeData(cb_data)

    def keyPressEvent(self, ev):
        print(ev, flush=True)
        key = ev.key()
        mod = ev.modifiers()
        if key == Qt.Key_C:
            self.clipboard_copy_html()
        elif key == Qt.Key_Comma:
            self.resize_to_left()
        elif key == Qt.Key_Period:
            self.resize_to_right()
        elif key == Qt.Key_M:
            self.resize_full()
        elif key == Qt.Key_R:
            self.load_document()
        elif key == Qt.Key_T:
            self.toggle_on_top()
        elif key == Qt.Key_W and mod == Qt.ControlModifier:
            self.close()
        elif key == Qt.Key_H or key == Qt.Key_Question:
            self.helpDialog()
        else:
            super().keyPressEvent(ev)

    def helpDialog(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowFlags(Qt.Sheet)
        msg_box.setText("Keyboard shortcuts")
        msg_box.setInformativeText("""
            <table>
            <tr><td> c  <td> Copy HTML to clipboard
            <tr><td> m  <td> Reset full size
            <tr><td> ,  <td> Resize left
            <tr><td> .  <td> Resize right
            <tr><td> t  <td> Toggle "stay on top"
            <tr><td> r  <td> Reload document
            <tr><td> ⌘w <td> Close window
            <tr><td> h &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <td> Help
            <tr><td> ? &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <td> Help
            </table>
        """)
        msg_grid = msg_box.findChild(QGridLayout)
        msg_icon_label = msg_box.findChild(QLabel, "qt_msgboxex_icon_label")
        msg_grid.removeWidget(msg_icon_label)
        msg_label = msg_box.findChild(QLabel, "qt_msgbox_label")
        msg_grid.removeWidget(msg_label)
        msg_grid.addWidget(msg_label, 0, 0, 1, 2)
        msg_info_label = msg_box.findChild(QLabel, "qt_msgbox_informativelabel")
        msg_grid.removeWidget(msg_info_label)
        msg_grid.addWidget(msg_info_label, 1, 0, 1, 2)
        msg_label.setContentsMargins(10, 10, 10, 0)
        msg_info_label.setContentsMargins(10, 0, 10, 0)
        msg_box.setContentsMargins(2, 0, 0, 0)
        msg_box.open()


########################################################################
# PdfViewer
########################################################################

class PdfViewer(
    qpageview.link.LinkViewMixin,
    qpageview.shadow.ShadowViewMixin,
    qpageview.highlight.HighlightViewMixin,
    qpageview.widgetoverlay.WidgetOverlayViewMixin,
    qpageview.view.View
):

    def __init__(self, app, file=None, key=None, old_viewer=None):
        super().__init__()
        self.app = app
        if file is not None:
            self.file = Path(file).resolve()
            self.gen_key()
            self.siblings = [ self.key ]
            for v in self.app.viewers.items():
                if v.file == self.file:
                    sibs = [ s for s in v.siblings ]
                    for skey in sibs:
                        if skey in self.app.viewers:
                            self.app.viewers[skey].siblings.insert(0, self.key)
                    self.siblings += sibs
                    break
            self.posHist = []
            self.posHistIdx = -1
            self.synctex_dir = None
            self.hscroll_lock = True
            self.on_top = False
        elif old_viewer is not None:
            old_props = qpageview.view.ViewProperties()
            old_props.get(old_viewer)
            self.file = old_viewer.file
            self.gen_key()
            sibs = [ s for s in old_viewer.siblings ]
            idx = sibs.index(old_viewer.key)+1
            for skey in sibs:
                if skey in self.app.viewers:
                    self.app.viewers[skey].siblings.insert(idx, self.key)
            self.siblings = [ s for s in old_viewer.siblings ]
            self.posHist = old_viewer.posHist
            self.posHistIdx = old_viewer.posHistIdx
            self.synctex_dir = old_viewer.synctex_dir
            self.hscroll_lock = old_viewer.hscroll_lock
            self.on_top = old_viewer.on_top
        else:
            return
        self.init_window()
        self.init_menu()
        self.init_tab_bar()
        #self.init_magnifier()
        self.init_rubberband()
        self.init_view()
        self.init_document()
        if old_viewer is not None:
            self.setGeometry(old_viewer.geometry())
            self.size_state = old_viewer.size_state
        self.show()
        if old_viewer is not None:
            old_props.set(self)
            # self.setPosition(old_props.position)

    def duplicate(self, show=True):
        new_viewer = PdfViewer(self.app, old_viewer=self)
        self.app.viewers[new_viewer.key] = new_viewer
        for skey in self.siblings:
            if skey != new_viewer.key:
                if skey in self.app.viewers:
                    self.app.viewers[skey].update_tab_bar()

    def gen_key(self):
        key = self.file
        i = 0
        while key in self.app.viewers:
            i += 1
            key = f"{self.file}_@_{i}"
        self.key = key

    def init_window(self):
        self.toggle_on_top(self.on_top, False)
        self.init_size()
        self.kineticScrollingEnabled = False
        self.setWindowTitle(f"{self.file.name} ({self.file.parent})")

    def init_menu(self):
        self.menu_bar = QMenuBar(self)
        self.toc_menu = self.menu_bar.addMenu(self.file.name)
        self.currentPageNumberChanged.connect(self.update_menu_title)
        self.pageCountChanged.connect(self.update_menu_title)

    def update_menu_title(self):
        self.toc_menu.setTitle(
            f"{self.file.name} ({self.currentPageNumber()}/{self.pageCount()})"
        )

    def init_tab_bar(self):
        self.tab_bar = None
        if len(self.siblings) <= 1:
            return
        self.tab_bar = QWidget(self)
        tab_bar_layout = QVBoxLayout()
        tab_bar_layout.setContentsMargins(4,4,0,0)
        tab_bar_layout.setSpacing(4);
        for i, skey in enumerate(self.siblings):
            button = QPushButton(f"{i+1}")
            button.setFixedWidth(30)
            if self.key == skey:
                button.setStyleSheet("""
                    padding: 3px;
                    color: white;
                    background-color: #2B384D;
                    border: 1px solid black;
                    border-radius: 4px;
                """)
            else:
                button.setStyleSheet("""
                    padding: 3px;
                    color: black;
                    background-color: #A8B9CA;
                    border: 1px solid black;
                    border-radius: 4px;
                """)
                button.clicked.connect(lambda state, j=i: self.raise_sibling(j))
            tab_bar_layout.addWidget(button)
        self.tab_bar.setLayout(tab_bar_layout)
        self.tab_bar.show()

    def update_tab_bar(self):
        self.siblings = [
            s
            for s in self.siblings
            if s in self.app.viewers
        ]
        if self.tab_bar is not None:
            self.tab_bar.setParent(None)
            self.tab_bar = None
        self.init_tab_bar()

    def raise_sibling(self, i):
        try:
            skey = self.siblings[i]
            viewer = self.app.viewers[skey]
        except:
            return
        viewer.raise_()
        viewer.activateWindow()

    def toggle_on_top(self, on_top=None, show=True):
        if on_top is None:
            self.on_top = not self.on_top
        else:
            self.on_top = on_top
        flags = Qt.CustomizeWindowHint
        if self.on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        if show:
            self.show()

    def init_size(self):
        ag = self.app.desktop().availableGeometry()
        if ag.height() > 1400:
            self.size_state = [2, 1]
            self.resize_to_right()
        else:
            self.size_state = [1, 0]
            self.resize_full()

    def resize_full(self):
        ag = self.app.desktop().availableGeometry()
        self.move(ag.left(), ag.top())
        self.resize(ag.width(), ag.height())
        self.size_state = [1, 0]

    def resize_to_left(self):
        ag = self.app.desktop().availableGeometry()
        if self.size_state == [1, 0]:
            self.move(ag.left(), ag.top())
            self.resize(ag.width()//2, ag.height())
            self.size_state = [2, 0]
        elif self.size_state == [2, 0]:
            self.move(ag.left(), ag.top())
            self.resize(8*ag.width()//19, ag.height())
            self.size_state = [2.375, 0]
        elif self.size_state == [2, 1]:
            self.move(ag.left(), ag.top())
            self.size_state = [2, 0]
        elif self.size_state == [2.375, 0]:
            self.move(ag.left(), ag.top())
            self.resize(ag.width()//3, ag.height())
            self.size_state = [3, 0]
        elif self.size_state == [2.375, 1]:
            self.move(ag.left(), ag.top())
            self.size_state = [2.375, 0]
        elif self.size_state == [3, 1]:
            self.move(ag.left(), ag.top())
            self.size_state = [3, 0]
        elif self.size_state == [3, 2]:
            self.move(ag.left()+ag.width()//3+1, ag.top())
            self.size_state = [3, 1]
        pos = self.position()
        self.setPosition(qpageview.view.Position(
            pos.pageNumber, 0.5, pos.y
        ))

    def resize_to_right(self):
        ag = self.app.desktop().availableGeometry()
        if self.size_state == [1, 0]:
            self.move(ag.left()+ag.width()//2+1,ag.top())
            self.resize(ag.width()//2, ag.height())
            self.size_state = [2, 1]
        elif self.size_state == [2, 0]:
            self.move(ag.left()+ag.width()//2+1,ag.top())
            self.size_state = [2, 1]
        elif self.size_state == [2, 1]:
            self.move(ag.left()+11*ag.width()//19+1,ag.top())
            self.resize(8*ag.width()//19, ag.height())
            self.size_state = [2.375, 1]
        elif self.size_state == [2.375, 0]:
            self.move(ag.left()+11*ag.width()//19+1,ag.top())
            self.size_state = [2.375, 1]
        elif self.size_state == [2.375, 1]:
            self.move(ag.left()+2*ag.width()//3+1,ag.top())
            self.resize(ag.width()//3, ag.height())
            self.size_state = [3, 2]
        elif self.size_state == [3, 0]:
            self.move(ag.left()+ag.width()//3+1,ag.top())
            self.size_state = [3, 1]
        elif self.size_state == [3, 1]:
            self.move(ag.left()+2*ag.width()//3+1,ag.top())
            self.size_state = [3, 2]
        pos = self.position()
        self.setPosition(qpageview.view.Position(
            pos.pageNumber, 0.5, pos.y
        ))

    def init_magnifier(self):
        m = qpageview.magnifier.Magnifier()
        self.setMagnifier(m)

    def init_rubberband(self):
        self.text_selector = qpageview.rubberband.Rubberband()
        # FIXME: disabled for now, as it interfeers with other left mouse clicks.
        # self.text_selector.showbutton = Qt.LeftButton
        self.text_selector.selectionChanged.connect(self.selectionChangedEvent)
        self.setRubberband(self.text_selector)

    def init_view(self):
        if self.size_state == [1, 0]:
            self.setViewMode(qpageview.FitWidth)
            self.strictPagingEnabled = False
            self.zoomOut(factor=1.1**2)
        else:
            self.setViewMode(qpageview.FitHeight)
            self.strictPagingEnabled = True
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def init_document(self):
        self._document_loaded = False
        self.load_document()
        self.reloader_timer = QTimer()
        self.reloader_timer.timeout.connect(self.autoReloadEvent)
        self.reloader_timer.start(1000)

    def load_document(self):
        success = True
        self.movie_player = None
        self.web_view = None
        if self.file.suffix == ".pdf":
            # if self.file in self.app.documents:
            #     doc = self.app.documents[self.file]
            #     self.setDocument(doc)
            # else:
            #     self.loadPdf(str(self.file))
            #     self.app.documents[self.file] = self.document()
            self.loadPdf(str(self.file))
            success = self.document().document()
        elif self.file.suffix == ".svg":
            self.loadSvgs([str(self.file)])
        elif self.file.suffix == ".gif":
            self.loadImages([str(self.file)])
            self.movie_player = MoviePlayer.make(self, str(self.file))
        # elif self.file.suffix == ".html":
        #     # self.loadImages([str(self.file)])
        #     self.web_view = HtmlViewer.make(self, str(self.file))
        else:
            self.loadImages([str(self.file)])
        if success:
            self._document_loaded = True
            self._document_load_error = None
            self._document_mtime = self.file.stat().st_mtime
            self.populate_toc_menu()
        else:
            self._document_loaded = False
            # self._document_load_error = err.getvalue()
            self._document_load_error = "error"
            self._document_mtime = -1

    def autoReloadEvent(self):
        if self.file.exists():
            if self._document_loaded:
                new_mtime = self.file.stat().st_mtime
                if new_mtime > self._document_mtime:
                    self.reload()
                    self.populate_toc_menu()
                    self._document_mtime = new_mtime
            else:
                self.load_document()
        else:
            self._document_mtime = -1
            if self._document_loaded:
                self.clear()
                self._document_loaded = False
                self._document_load_error = None

    def populate_toc_menu(self):
        self.toc_menu.clear()
        def add_toc_action(text, page_num=0, x=0, y=0):
            pos = qpageview.view.Position(pageNumber = page_num, x = x, y = y)
            act = self.toc_menu.addAction(text)
            act.triggered.connect(lambda state, p=pos: self.goToPos(p))
        if self.file.suffix != ".pdf":
            add_toc_action("Image file")
            return
        add_toc_action("Table of contents")
        doc = self.document().document()
        if not doc:
            return
        toc = doc.toc()
        if not toc:
            return
        toc_item = doc.toc().firstChild()
        while not toc_item.isNull():
            toc_el = toc_item.toElement()
            toc_text = toc_el.tagName()
            toc_dest = toc_el.attribute("DestinationName")
            if not toc_dest:
                continue
            toc_dest = doc.linkDestination(toc_dest)
            add_toc_action(
                toc_text,
                page_num = toc_dest.pageNumber(),
                x = toc_dest.left(),
                y = toc_dest.top(),
            )
            toc_item = toc_item.nextSibling()

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
            if self.strictPagingEnabled:
                num = self.currentPageNumber()
                if not ((page_num-1) <= num <= page_num):
                    self.goToPageAux(page_num)
            else:
                self.setPosition((page_num, 0.5, y))
            self.highlight(
                { page: [area] },
                msec = 10000,
                scroll = True,
                margins = margins,
            )

    def selectionChangedEvent(self, ev):
        text = self.text_selector.selectedText()
        self.app.clipboard().setText(text)

    def keyPressEvent(self, ev):
        key = ev.key()
        mod = ev.modifiers()
        if key == Qt.Key_Equal:
            self.strictPagingEnabled = False
            self.zoomIn()
        elif key == Qt.Key_Minus:
            self.strictPagingEnabled = False
            self.zoomOut()
        elif mod == Qt.ControlModifier and (Qt.Key_1 <= key <= Qt.Key_9):
            idx = key - Qt.Key_1
            self.raise_sibling(idx)
        elif self.movie_player and key == Qt.Key_Space:
            if self.movie_player.state() == QMovie.NotRunning:
                self.movie_player.start()
            elif self.movie_player.state() == QMovie.Running:
                self.movie_player.setPaused(True)
            elif self.movie_player.state() == QMovie.Paused:
                self.movie_player.setPaused(False)
        elif self.movie_player and key == Qt.Key_BracketLeft:
            self.movie_player.jumpToFrame(0)
        elif self.movie_player and key == Qt.Key_BracketRight:
            last_frame = self.movie_player.frameCount() - 1
            self.movie_player.jumpToFrame(last_frame)
        elif self.movie_player and key == Qt.Key_Period:
            pass
        elif key == Qt.Key_0:
            #self.setZoomFactor(1.0)
            if (
                self.pageLayoutMode() != "single"
                or (
                    0.8
                    <
                    (11*self.width()/self.height()/8.5)
                    <
                    1.2
                )
            ):
                self.setViewMode(qpageview.FitHeight)
                self.strictPagingEnabled = True
            else:
                self.setViewMode(qpageview.FitWidth)
                self.strictPagingEnabled = False
        elif key == Qt.Key_1:
            self.setPageLayoutMode("single")
        elif key == Qt.Key_2:
            self.setPageLayoutMode("double_right")
        elif key == Qt.Key_3:
            self.setPageLayoutMode("double_left")
        elif self.pageLayoutMode() != "single" and key == Qt.Key_PageUp:
            num = self.currentPageNumber()
            if num > 2:
                self.setCurrentPageNumber(num - 2)
        elif self.pageLayoutMode() != "single" and key == Qt.Key_PageDown:
            num = self.currentPageNumber()
            if num < self.pageCount() - 1:
                self.setCurrentPageNumber(num + 2)
        elif key == Qt.Key_S:
            if self.continuousMode():
                self.setContinuousMode(False)
        elif key == Qt.Key_C:
            if not self.continuousMode():
                self.setContinuousMode(True)
        elif not self.continuousMode() and key == Qt.Key_Up:
            num = self.currentPageNumber()
            if num > 1 and self.pageLayoutMode() != "single":
                self.setCurrentPageNumber(num - 2)
            elif num > 0:
                self.setCurrentPageNumber(num - 1)
        elif not self.continuousMode() and key == Qt.Key_Down:
            num = self.currentPageNumber()
            if num < self.pageCount()+1 and self.pageLayoutMode() != "single":
                self.setCurrentPageNumber(num + 2)
            elif num < self.pageCount():
                self.setCurrentPageNumber(num + 1)
        elif key == Qt.Key_Home:
            self.goToPos(qpageview.view.Position(0, 0.5, 0))
        elif key == Qt.Key_End:
            self.goToPos(qpageview.view.Position(self.pageCount(), 0.5, 1))
        elif key == Qt.Key_G:
            self.goToPageDialog()
        elif key == Qt.Key_BracketLeft:
            self.goToPrevPos()
        elif key == Qt.Key_BracketRight:
            self.goToNextPos()
        elif key == Qt.Key_M:
            self.resize_full()
        elif key == Qt.Key_Comma:
            self.resize_to_left()
        elif key == Qt.Key_Period:
            self.resize_to_right()
        elif key == Qt.Key_T:
            self.toggle_on_top()
        elif key == Qt.Key_L:
            self.hscroll_lock = not self.hscroll_lock
        # elif key == Qt.Key_Q and mod == Qt.ControlModifier:
        #     self.app.quit()
        elif key == Qt.Key_R:
            print("reload!")
            self.reload()
            self.populate_toc_menu()
        elif key == Qt.Key_P and mod == Qt.ControlModifier:
            self.print()
        elif key == Qt.Key_P:
            self.openInPreview()
        elif key == Qt.Key_D:
            self.duplicate()
        elif key == Qt.Key_W and mod == Qt.ControlModifier:
            self.close()
        elif key == Qt.Key_H or key == Qt.Key_Question:
            self.helpDialog()
        else:
            super().keyPressEvent(ev)

    def helpDialog(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowFlags(Qt.Sheet)
        msg_box.setText("Keyboard shortcuts")
        msg_box.setInformativeText("""
            <table>
            <tr><td> =  <td> Zoom in 
            <tr><td> -  <td> Zoom out
            <tr><td> 0  <td> Reset zoom
            <tr><td> c  <td> Continuous mode
            <tr><td> s  <td> Single page mode
            <tr><td> 1  <td> Single page layout
            <tr><td> 2  <td> Double page layout (right)
            <tr><td> 3  <td> Double page layout (left)
            <tr><td> g  <td> Go to page
            <tr><td> [  <td> Go previous
            <tr><td> ]  <td> Go next
            <tr><td> m  <td> Reset full size
            <tr><td> ,  <td> Resize left
            <tr><td> .  <td> Resize right
            <tr><td> t  <td> Toggle "stay on top"
            <tr><td> l  <td> Toggle horizontal scroll lock
            <tr><td> r  <td> Reload document
            <tr><td> p  <td> Open in Preview app
            <tr><td> ⌘p <td> Print (using Qt)
            <tr><td> d  <td> Duplicate window
            <tr><td> ⌘w <td> Close window
            <tr><td> h &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <td> Help
            <tr><td> ? &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <td> Help
            </table>
        """)
        msg_grid = msg_box.findChild(QGridLayout)
        msg_icon_label = msg_box.findChild(QLabel, "qt_msgboxex_icon_label")
        msg_grid.removeWidget(msg_icon_label)
        msg_label = msg_box.findChild(QLabel, "qt_msgbox_label")
        msg_grid.removeWidget(msg_label)
        msg_grid.addWidget(msg_label, 0, 0, 1, 2)
        msg_info_label = msg_box.findChild(QLabel, "qt_msgbox_informativelabel")
        msg_grid.removeWidget(msg_info_label)
        msg_grid.addWidget(msg_info_label, 1, 0, 1, 2)
        msg_label.setContentsMargins(10, 10, 10, 0)
        msg_info_label.setContentsMargins(10, 0, 10, 0)
        msg_box.setContentsMargins(2, 0, 0, 0)
        msg_box.open()

    def linkClickEvent(self, ev, page, link):
        if link.url:
            webbrowser.open(link.url)
            return
        try:
            dest = link.linkobj.destination()
            pos = qpageview.view.Position(
                pageNumber = dest.pageNumber(),
                x = dest.left(),
                y = dest.top(),
            )
        except:
            return
        self.goToPos(pos)

    def savePos(self):
        curPos = self.position()
        if not self.posHist:
            self.posHistIdx = 0
            self.posHist.append(curPos)
        if self.posHist[self.posHistIdx] != curPos:
            self.posHistIdx += 1
            self.posHist[self.posHistIdx:] = [curPos]

    def goToPos(self, pos):
        self.savePos()
        if self.hscroll_lock:
            self.setPosition(qpageview.view.Position(
                pos.pageNumber, 0.5, pos.y
            ))
        else:
            self.setPosition(pos)
        self.savePos()

    def goToNextPos(self):
        if not self.posHist or self.posHistIdx >= len(self.posHist)-1:
            return
        self.posHistIdx += 1
        self.setPosition(self.posHist[self.posHistIdx])

    def goToPrevPos(self):
        if not self.posHist or self.posHistIdx <= 0:
            return
        self.posHistIdx -= 1
        self.setPosition(self.posHist[self.posHistIdx])

    def goToPageDialog(self):
        n0 = self.currentPageNumber()
        n, ok = QInputDialog().getInt(
            self,
            "Go to page",
            "Page number:",
            value = n0,
            min = 1,
            max = self.pageCount(),
            step = 1,
            flags = Qt.Sheet,
        )
        if ok and n != n0:
            self.savePos()
            self.goToPageAux(n)
            self.savePos()

    def goToPageAux(self, n):
        self.setCurrentPageNumber(n)
        pos = self.position()
        self.setPosition(qpageview.view.Position(
            pos.pageNumber, 0.5, pos.y
        ))

    def openInPreview(self):
        subprocess.call(["open", "-a", "Preview", self.file])

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
                self.app.synctex_queue.append(("edit", page_num, x, y, str(self.file), self.synctex_dir))
                self.app.proc_synctex_queue()
                return
        super().mousePressEvent(ev)

    def wheelEvent(self, ev):
        if not self.hscroll_lock:
            super().wheelEvent(ev)
        else:
            angleDelta = ev.angleDelta()
            angleDelta.setX(0);
            super().wheelEvent(QWheelEvent(
                ev.position(),
                ev.globalPosition(),
                ev.pixelDelta(),
                angleDelta,
                ev.buttons(),
                ev.modifiers(),
                ev.phase(),
                ev.inverted(),
            ))

    def closeEvent(self, ev):
        del self.app.viewers[self.key]
        for skey in reversed(self.siblings):
            if skey in self.app.viewers:
                self.app.viewers[skey].update_tab_bar()
        # for viewer in self.app.viewers.values():
        #     if self.file == viewer.file:
        #         break
        # else:
        #     del self.app.documents[self.file]


########################################################################
# main
########################################################################

if __name__ == "__main__":
    PdfViewerApp.run()#"/Users/roi/test/old/arc-fiber-2022-1208.pdf")
