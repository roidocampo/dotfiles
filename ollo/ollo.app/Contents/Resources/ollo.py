
########################################################################
# imports
########################################################################

import os
import sys
import tempfile
import time

from collections import namedtuple
from pathlib import Path

import djvu.decode as djvud
import fitz

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

########################################################################
# debug
########################################################################

if __debug__:

    import inspect
    from datetime import datetime

    def deb(*args, **kws):
        stamp = datetime.now().isoformat()
        nline = inspect.currentframe().f_back.f_lineno
        infos = ", ".join(
            [ f"{v}" for v in args ]
            + [ f"{k}: {v}" for k, v in kws.items() ]
        )
        if infos:
            infos = " " + infos
        print(f"[{stamp}] [{nline}]{infos}")

########################################################################
# EmptyPage
########################################################################

class EmptyPage(QWidget):

    def __init__(self, document_view, page_num, *args, **kws):
        if 'parent' not in kws:
            kws['parent'] = document_view.container
        super().__init__(*args, **kws)
        self.document_view = document_view
        self.document = document_view.document
        self.page_num = page_num
        self.page_ratio = 11/8.5
        self.base_canvas_width = 1100
        self.zoom = 1.
        self.recompute_size()
        self._init_page_()

    def _init_page_(self):
        label = QLabel(f"# {self.page_num}", parent=self)
        label.move(3,3)

    def set_zoom(self, new_zoom):
        if self.zoom != new_zoom:
            self.zoom = new_zoom
        self.recompute_size()

    def recompute_size(self):
        self.canvas_width = int(self.base_canvas_width * self.zoom)
        self.canvas_height = int(self.base_canvas_width * self.page_ratio * self.zoom)
        self.setFixedSize(self.canvas_width, self.canvas_height)

    def get_image(self):
        try:
            img = self.document.get_image(self.page_num, self.zoom)
        except KeyError:
            img = self.generate_image()
            self.document.save_image(self.page_num, self.zoom, img)
        return img

    def generate_image(self):
        return None

    def paintEvent(self, e):
        painter = QPainter(self)
        rect = QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, Qt.white)
        self.paint_page(painter)
        painter.drawRect(rect)

    def paint_page(self, painter):
        img = self.get_image()
        if img is not None:
            painter.drawImage(0,0,img)

########################################################################
# EmptyDocucment
########################################################################

class EmptyDocucment:

    page_class = EmptyPage
    cache_size_limit = 20

    def __init__(self, file_name):
        self.file_name = file_name
        self.images = {}
        self._init_document_()

    def _init_document_(self):
        self.num_pages = 47
        pass

    def save_image(self, page_num, zoom, img):
        while len(self.images) > self.cache_size_limit:
            k = next(iter(self.images))
            self.images.pop(k)
        self.images[page_num, zoom] = img

    def get_image(self, page_num, zoom):
        return self.images[page_num, zoom]

########################################################################
# DocumentView
########################################################################

class DocumentView(QScrollArea):

    document_class = EmptyDocucment

    def __init__(self, file_name, *args, **kws):
        super().__init__(*args, **kws)
        self.file_name = file_name
        if __debug__: deb(file_name=file_name)
        self.zoom = 1.
        self._init_document_()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setAlignment(Qt.AlignCenter)
        self.container = container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        container.setLayout(self.layout)
        self.setWidget(container)
        self._init_pages_()

    def _init_document_(self):
        self.document = self.document_class(self.file_name)

    def _init_pages_(self):
        self.pages = []
        p_class = self.document.page_class
        if __debug__: deb(pages=self.document.num_pages)
        for i in range(self.document.num_pages):
            p = p_class(self, i)
            self.pages.append(p)
            self.layout.addWidget(p)

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key_Minus:
            return self.zoom_out()
        if k == Qt.Key_Equal:
            return self.zoom_in()
        if k == Qt.Key_0:
            return self.reset_zoom()
        super().keyPressEvent(e)

    def zoom_out(self):
        if self.zoom > 0.5:
            self.zoom -= 0.1
            self.zoom_pages()

    def zoom_in(self):
        if self.zoom < 5:
            self.zoom += 0.1
            self.zoom_pages()

    def reset_zoom(self):
        if self.zoom != 1.:
            self.zoom = 1.
            self.zoom_pages()

    def zoom_pages(self):
        for p in self.pages:
            p.set_zoom(self.zoom)

########################################################################
# PdfPage
########################################################################

class PdfPage(EmptyPage):

    def _init_page_(self):
        self._pdfpage = None

    @property
    def pdfpage(self):
        if self._pdfpage is None:
            p = self.document.pdfdoc[self.page_num]
            self._pdfpage = d = p.getDisplayList()
            self.page_ratio = d.rect.height / d.rect.width
            self.recompute_size()
        return self._pdfpage

    def generate_image(self):
        r = self.canvas_width / self.pdfpage.rect.width
        m = fitz.Matrix(r, r)
        pix = self.pdfpage.getPixmap(matrix=m)
        fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        return img

########################################################################
# PdfDocument
########################################################################

class PdfDocument(EmptyDocucment):

    page_class = PdfPage

    def _init_document_(self):
        self.pdfdoc = fitz.open(self.file_name)
        self.num_pages = self.pdfdoc.pageCount

########################################################################
# PdfView
########################################################################

class PdfView(DocumentView):
    document_class = PdfDocument

########################################################################
# DjvuPage
########################################################################

class DjvuPage(EmptyPage):

    def _init_page_(self):
        self._djvupage = None

    @property
    def djvupage(self):
        if self._djvupage is None:
            p = self.document.djvudoc.pages[self.page_num]
            pj = p.decode(wait = True)
            self.page_ratio = pj.height / pj.width
            self.recompute_size()
            self._djvupage = pj
        return self._djvupage

    def generate_image(self):
        dpf = djvud.PixelFormatRgbMask(0xFF0000, 0xFF00, 0xFF, 0xFF000000, bpp=32)
        dpf.rows_top_to_bottom = 1
        dpf.y_top_to_bottom = 0
        pj = self.djvupage
        data = pj.render(
            djvud.RENDER_COLOR,
            (0, 0, self.canvas_width, self.canvas_height),
            (0, 0, self.canvas_width, self.canvas_height),
            dpf,
        )
        img = QImage(data, self.canvas_width, self.canvas_height, QImage.Format_RGB32)
        return img

########################################################################
# DjvuDocument
########################################################################

class DjvuDocument(EmptyDocucment):

    page_class = DjvuPage

    def _init_document_(self):
        ctx = djvud.Context()
        uri = djvud.FileURI(self.file_name)
        self.djvudoc = doc = ctx.new_document(uri)
        doc.decoding_job.wait()
        self.num_pages = len(doc.pages)

########################################################################
# DjvuView
########################################################################

class DjvuView(DocumentView):
    document_class = DjvuDocument

########################################################################
# create_view
########################################################################

def create_view(file):
    file_path = Path(file)
    file_name = file_path.stem
    file_ext = file_path.suffix
    if file_ext == ".pdf":
        view_class = PdfView
    elif file_ext == ".djvu":
        view_class = DjvuView
    else:
        view_class = DocumentView
    view = view_class(file)
    return file_name, view

########################################################################
# SideBar
########################################################################

class SideBar(QListWidget):

    _css = """
        QListWidget {
            border: none;
            background-color : #A4B9CC;
            color: black;
            border-right     : 1px solid black;
        }

        QListWidget::icon {
            qproperty-icon: none;
        }
            
        QListWidget::item {
            background-color : #A4B9CC;
            padding          : 5px;
            padding-left     : 8px;
            border-bottom    : 1px solid black;
            border-left      : none;
        }

        QListWidget::item:selected {
            color: black;
            padding-left: 3px;
            border-left: 5px solid #30445F;
        }

    """

    def __init__(self, viewer, *args, **kws):
        self.viewer = viewer
        super().__init__(*args, **kws)
        self.setMaximumWidth(200)
        self.setWordWrap(True)
        self.setStyleSheet(self._css)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.itemClicked.connect(self.on_click)
        self.itemActivated.connect(self.on_click)

    @property
    def stack(self):
        return self.viewer.stack

    _data_key = 1000

    def add_tab(self, label, view):
        it = QListWidgetItem(label)
        it.setData(self._data_key, view)
        self.addItem(it)
        self.setCurrentItem(it)

    def remove_current_tab(self):
        row = self.currentRow()
        if row == -1:
            return
        it = self.takeItem(row)
        view = it.data(self._data_key)
        self.stack.removeWidget(view)
        del it

    def on_click(self, it):
        view = it.data(self._data_key)
        old_view = self.stack.currentWidget()
        if old_view:
            old_view.releaseKeyboard()
        self.stack.setCurrentWidget(view)
        view.grabKeyboard()

########################################################################
# ViewerMainWindow
########################################################################

class ViewerMainWindow(QMainWindow):

    def __init__(self, qapp, *args, **kws):
        if __debug__: deb("creating main window")
        super().__init__(*args, **kws)
        self.qapp = qapp
        for name, method in self.__class__.__dict__.items():
            if name.startswith("_init_"):
                method(self)

    def _init_qapp_(self):
        self.desktop = self.qapp.desktop()
        self.exec_ = self.qapp.exec_

    def _init_window_(self):
        sg = self.desktop.screenGeometry()
        ag = self.desktop.availableGeometry()
        self.setWindowFlags(Qt.CustomizeWindowHint)
        self.resize(ag.width(), ag.height())
        self.show()

    def _init_central_widget_(self):
        self.central_widget = cw = QWidget()
        self.layout = QHBoxLayout(cw)
        self.layout.setSizeConstraint(QLayout.SetMaximumSize)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        cw.setLayout(self.layout)
        self.setCentralWidget(cw)

    def _init_sidebar_(self):
        self.sidebar = SideBar(self)
        self.layout.addWidget(self.sidebar)

    def _init_view_stack_(self):
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)

    def _init_menu_(self):
        self.menu = menu = QMenuBar()
        self.file_menu = menu.addMenu("File")
        self.hola_act = QAction("O ollo que todo o ve")
        self.hola_act.setMenuRole(QAction.ApplicationSpecificRole)
        self.close_act = QAction("Close")
        self.close_act.setShortcuts(QKeySequence.Close);
        self.close_act.triggered.connect(self.close_view)
        self.file_menu.addAction(self.close_act)
        self.file_menu.addAction(self.hola_act)

    def close_view(self, *arg):
        self.sidebar.remove_current_tab()

    def add_view(self, file):
        file_name, view = create_view(file)
        self.stack.addWidget(view)
        self.stack.setCurrentWidget(view)
        label = file_name.replace("_", " ")
        self.sidebar.add_tab(label, view)
        view.grabKeyboard()
        self.raise_()

########################################################################
# RPCTManager
########################################################################

class RPCManager:

    base_folder = Path.home() / ".ollo_rpc"
    pid_folder = base_folder / "pid"
    rpc_folder = base_folder / "rpc"

    def __init__(self, qapp):
        if __debug__: deb("creating rpc managaer")
        self.qapp = qapp
        self.own_pid = os.getpid()
        self.other_exists, self.server_pid = \
            self.check_for_other_instances()
        qapp.other_exists = self.other_exists
        if not self.other_exists:
            if __debug__: deb("creating pid file")
            self.init_pid_file()

    def check_for_other_instances(self):
        if __debug__: deb("checking for other instance")
        self.pid_folder.mkdir(parents=True, exist_ok=True)
        for pid_file in self.pid_folder.iterdir():
            if pid_file.is_file():
                try:
                    pid = int(pid_file.stem)
                except ValueError:
                    continue
                if self.pid_exists(pid):
                    if __debug__: deb("found other instance")
                    return True, pid
                else:
                    pid_file.unlink()
        if __debug__: deb("did not find other instance")
        return False, 0

    def pid_exists(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def init_pid_file(self):
        self.rpc_folder.mkdir(parents=True, exist_ok=True)
        self.pid = str(self.own_pid)
        self.pid_file = self.pid_folder / self.pid
        self.pid_file.touch(exist_ok=True)

    def start_listening(self):
        if __debug__: deb("creating rpc timer")
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_rpc)
        self.timer.start(500)

    def check_rpc(self):
        for f in self.rpc_folder.iterdir():
            if __debug__: deb(rpc_file=f)
            if f.is_file():
                try:
                    file_to_open = Path(f.read_text().strip())
                except:
                    continue
                finally:
                    f.unlink()
                if __debug__: deb(file_to_open=file_to_open)
                if file_to_open.is_file():
                    file_to_open = file_to_open.resolve()
                    self.qapp.open_file(file_to_open)

    def send_rpc_message(self, message):
        if __debug__: deb(f"rpc send: {message}")
        with tempfile.NamedTemporaryFile(
            mode='wt',
            dir=self.rpc_folder,
            delete=False,
        ) as rpc_file:
            if __debug__: deb(f"rpc file: {rpc_file.name}")
            rpc_file.write(message)

########################################################################
# EVENT_NAMES
########################################################################

EVENT_NAMES = { 0: "QEvent::None", 114: "QEvent::ActionAdded", 113: "QEvent::ActionChanged", 115: "QEvent::ActionRemoved", 99: "QEvent::ActivationChange", 121: "QEvent::ApplicationActivate", 122: "QEvent::ApplicationDeactivate", 36: "QEvent::ApplicationFontChange", 37: "QEvent::ApplicationLayoutDirectionChange", 38: "QEvent::ApplicationPaletteChange", 214: "QEvent::ApplicationStateChange", 35: "QEvent::ApplicationWindowIconChange", 68: "QEvent::ChildAdded", 69: "QEvent::ChildPolished", 71: "QEvent::ChildRemoved", 40: "QEvent::Clipboard", 19: "QEvent::Close", 200: "QEvent::CloseSoftwareInputPanel", 178: "QEvent::ContentsRectChange", 82: "QEvent::ContextMenu", 183: "QEvent::CursorChange", 52: "QEvent::DeferredDelete", 60: "QEvent::DragEnter", 62: "QEvent::DragLeave", 61: "QEvent::DragMove", 63: "QEvent::Drop", 170: "QEvent::DynamicPropertyChange", 98: "QEvent::EnabledChange", 10: "QEvent::Enter", 150: "QEvent::EnterEditFocus", 124: "QEvent::EnterWhatsThisMode", 206: "QEvent::Expose", 116: "QEvent::FileOpen", 8: "QEvent::FocusIn", 9: "QEvent::FocusOut", 23: "QEvent::FocusAboutToChange", 97: "QEvent::FontChange", 198: "QEvent::Gesture", 202: "QEvent::GestureOverride", 188: "QEvent::GrabKeyboard", 186: "QEvent::GrabMouse", 159: "QEvent::GraphicsSceneContextMenu", 164: "QEvent::GraphicsSceneDragEnter", 166: "QEvent::GraphicsSceneDragLeave", 165: "QEvent::GraphicsSceneDragMove", 167: "QEvent::GraphicsSceneDrop", 163: "QEvent::GraphicsSceneHelp", 160: "QEvent::GraphicsSceneHoverEnter", 162: "QEvent::GraphicsSceneHoverLeave", 161: "QEvent::GraphicsSceneHoverMove", 158: "QEvent::GraphicsSceneMouseDoubleClick", 155: "QEvent::GraphicsSceneMouseMove", 156: "QEvent::GraphicsSceneMousePress", 157: "QEvent::GraphicsSceneMouseRelease", 182: "QEvent::GraphicsSceneMove", 181: "QEvent::GraphicsSceneResize", 168: "QEvent::GraphicsSceneWheel", 18: "QEvent::Hide", 27: "QEvent::HideToParent", 127: "QEvent::HoverEnter", 128: "QEvent::HoverLeave", 129: "QEvent::HoverMove", 96: "QEvent::IconDrag", 101: "QEvent::IconTextChange", 83: "QEvent::InputMethod", 207: "QEvent::InputMethodQuery", 169: "QEvent::KeyboardLayoutChange", 6: "QEvent::KeyPress", 7: "QEvent::KeyRelease", 89: "QEvent::LanguageChange", 90: "QEvent::LayoutDirectionChange", 76: "QEvent::LayoutRequest", 11: "QEvent::Leave", 151: "QEvent::LeaveEditFocus", 125: "QEvent::LeaveWhatsThisMode", 88: "QEvent::LocaleChange", 176: "QEvent::NonClientAreaMouseButtonDblClick", 174: "QEvent::NonClientAreaMouseButtonPress", 175: "QEvent::NonClientAreaMouseButtonRelease", 173: "QEvent::NonClientAreaMouseMove", 177: "QEvent::MacSizeChange", 43: "QEvent::MetaCall", 102: "QEvent::ModifiedChange", 4: "QEvent::MouseButtonDblClick", 2: "QEvent::MouseButtonPress", 3: "QEvent::MouseButtonRelease", 5: "QEvent::MouseMove", 109: "QEvent::MouseTrackingChange", 13: "QEvent::Move", 197: "QEvent::NativeGesture", 208: "QEvent::OrientationChange", 12: "QEvent::Paint", 39: "QEvent::PaletteChange", 131: "QEvent::ParentAboutToChange", 21: "QEvent::ParentChange", 212: "QEvent::PlatformPanel", 217: "QEvent::PlatformSurface", 75: "QEvent::Polish", 74: "QEvent::PolishRequest", 123: "QEvent::QueryWhatsThis", 106: "QEvent::ReadOnlyChange", 199: "QEvent::RequestSoftwareInputPanel", 14: "QEvent::Resize", 204: "QEvent::ScrollPrepare", 205: "QEvent::Scroll", 117: "QEvent::Shortcut", 51: "QEvent::ShortcutOverride", 17: "QEvent::Show", 26: "QEvent::ShowToParent", 50: "QEvent::SockAct", 192: "QEvent::StateMachineSignal", 193: "QEvent::StateMachineWrapped", 112: "QEvent::StatusTip", 100: "QEvent::StyleChange", 87: "QEvent::TabletMove", 92: "QEvent::TabletPress", 93: "QEvent::TabletRelease", 171: "QEvent::TabletEnterProximity", 172: "QEvent::TabletLeaveProximity", 219: "QEvent::TabletTrackingChange", 22: "QEvent::ThreadChange", 1: "QEvent::Timer", 120: "QEvent::ToolBarChange", 110: "QEvent::ToolTip", 184: "QEvent::ToolTipChange", 194: "QEvent::TouchBegin", 209: "QEvent::TouchCancel", 196: "QEvent::TouchEnd", 195: "QEvent::TouchUpdate", 189: "QEvent::UngrabKeyboard", 187: "QEvent::UngrabMouse", 78: "QEvent::UpdateLater", 77: "QEvent::UpdateRequest", 111: "QEvent::WhatsThis", 118: "QEvent::WhatsThisClicked", 31: "QEvent::Wheel", 132: "QEvent::WinEventAct", 24: "QEvent::WindowActivate", 103: "QEvent::WindowBlocked", 25: "QEvent::WindowDeactivate", 34: "QEvent::WindowIconChange", 105: "QEvent::WindowStateChange", 33: "QEvent::WindowTitleChange", 104: "QEvent::WindowUnblocked", 203: "QEvent::WinIdChange", 126: "QEvent::ZOrderChange", }

########################################################################
# ViewerApp
########################################################################

class ViewerApp(QApplication):

    @classmethod
    def run(cls, argv=None):
        if __debug__: deb("starting viewer app")
        if __debug__: deb(argv=argv)
        if argv is None:
            argv = sys.argv
        app_instance = cls(argv)
        if app_instance.other_exists:
            if __debug__: deb("quitting")
        else:
            if __debug__: deb("starting qt loop")
            exit_code = app_instance.exec_()
            if __debug__: deb(exit_code=exit_code)
        del app_instance

    def __init__(self, argv, *args, **kws):
        self.rpc_manager = RPCManager(self)
        if not self.other_exists:
            if __debug__: deb("creating qt app")
            super().__init__(argv, *args, **kws)
            self.main_window = ViewerMainWindow(self)
            self.open_argv(argv)
            self.rpc_manager.start_listening()

    def event(self, e):
        t = e.type()
        if __debug__:
            if t in EVENT_NAMES:
                deb(EVENT_NAMES[t], f"({t})")
            else:
                deb("???", f"({t})")
        if t == QEvent.FileOpen:
            file = e.file()
            if __debug__: deb(f"opening {file}")
            self.open_file(file)
            return True
        return super().event(e)

    def open_argv(self, argv):
        if __debug__: deb (f"processing argv[1:]: {argv[1:]}")
        for arg in argv[1:]:
            if __debug__: deb (f"processing arg: {arg}")
            file = Path(arg)
            if file.exists():
                file = file.resolve()
                self.open_file(file)

    def open_file(self, file):
        self.main_window.add_view(file)

########################################################################
# RemoteOpenerApp
########################################################################

class RemoteOpenerApp(QApplication):

    @classmethod
    def run(cls, argv=None):
        if __debug__: deb("starting remote opener app")
        if __debug__: deb(argv=argv)
        if argv is None:
            argv = sys.argv
        app_instance = cls(argv)
        if __debug__: deb("starting qt loop")
        exit_code = app_instance.exec_()
        if __debug__: deb(exit_code=exit_code)
        del app_instance

    def __init__(self, argv, *args, **kws):
        self.rpc_manager = RPCManager(self)
        if __debug__: deb("creating qt app")
        super().__init__(argv, *args, **kws)
        self.open_argv(argv)
        QTimer.singleShot(10*1000, self.quit)

    def event(self, e):
        t = e.type()
        if __debug__:
            if t in EVENT_NAMES:
                deb(EVENT_NAMES[t], f"({t})")
            else:
                deb("???", f"({t})")
        if t == QEvent.FileOpen:
            file = e.file()
            if __debug__: deb(f"opening {file}")
            self.open_file(file)
            return True
        return super().event(e)

    def open_argv(self, argv):
        if __debug__: deb (f"processing argv[1:]: {argv[1:]}")
        for arg in argv[1:]:
            if __debug__: deb (f"processing arg: {arg}")
            self.open_file(arg)

    def open_file(self, file):
        file = Path(file)
        if file.is_file():
            file = str(file.resolve())
            self.rpc_manager.send_rpc_message(file)

########################################################################
# main
########################################################################

def main():
    if __debug__: deb("ollo starting")
    argv = []
    app = ViewerApp
    for arg in sys.argv:
        if arg == "--remote-open":
            app = RemoteOpenerApp
        else:
            argv.append(arg)
    app.run(argv)

########################################################################
#
########################################################################

if __name__ == "__main__":
    main()

