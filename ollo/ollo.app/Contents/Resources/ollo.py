
########################################################################
# imports
########################################################################

import itertools
import os
import sys
import tempfile
import time
import unicodedata

from pathlib import Path

import djvu.decode as djvud
import djvu.sexpr as djvue
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
# event_filter
########################################################################

class event_filter(QObject):

    def __init__(self, filter_function):
        super().__init__()
        self.filter_function = filter_function

    def eventFilter(self, obj, event):
        return self.filter_function(obj, event)

########################################################################
# FoundText(QWidget):
########################################################################

class FoundText(QWidget):

    def __init__(self, needle, page, rel_rect):
        super().__init__(parent=page)
        self.setCursor(Qt.PointingHandCursor)
        self.active = False
        self.needle = needle
        self.page = page
        self.rel_rect = rel_rect
        self.recompute_size()
        self._next = None
        self._previous = None

    def recompute_size(self):
        self.setGeometry(self.abs_rect())

    def abs_rect(self):
        (x0, y0, x1, y1) = self.rel_rect
        return QRect(
            QPoint(
                int(x0 * self.page.canvas_width),
                int(y0 * self.page.canvas_height),
            ),
            QPoint(
                int(x1 * self.page.canvas_width),
                int(y1 * self.page.canvas_height),
            ),
        )

    def paintEvent(self, e):
        painter = QPainter(self)
        rect = QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, QColor("#44ffcccc"))
        pen = QPen(QColor("#ff0000"))
        if self.active:
            pen.setWidth(3)
        painter.setPen(pen)
        painter.drawRect(rect)
        #painter.fillRect(rect, QColor("#4499cccc"))

    def trigger_next_page_find(self):
        page = self.page
        pages = self.page.document_view.pages
        p = pages.index(page) + 1
        if p >= len(pages):
            return
        page = pages[p]
        page._find(self.needle)

    def next(self):
        if self._next is None:
            page = self.page
            i = page.found_items.index(self)
            if i < len(page.found_items) - 1:
                i += 1
            else:
                i = 0
                pages = self.page.document_view.pages
                p = pages.index(page) + 1
                while True:
                    if p >= len(pages):
                        p = 0
                    page = pages[p]
                    page._find(self.needle)
                    if page.found_items:
                        break
                    p += 1
            self._next = page.found_items[i]
        return self._next

    def previous(self):
        if self._previous is None:
            page = self.page
            i = page.found_items.index(self)
            if i > 0:
                i -= 1
            else:
                i = -1
                pages = self.page.document_view.pages
                p = pages.index(page) - 1
                while True:
                    page = pages[p]
                    page._find(self.needle)
                    if page.found_items:
                        break
                    p -= 1
            self._previous = page.found_items[i]
        return self._previous


########################################################################
# DocLink
########################################################################

class DocLink(QWidget):

    def __init__(self, page, rel_rect, *link_data):
        super().__init__(parent=page)
        self.setCursor(Qt.PointingHandCursor)
        self.active = False
        self.page = page
        self.rel_rect = rel_rect
        self._init_link_(link_data)
        self.recompute_size()

    def _init_link_(self, link_data):
        self.link_data = link_data

    def recompute_size(self):
        self.setGeometry(self.abs_rect())

    def abs_rect(self):
        (x0, y0, x1, y1) = self.rel_rect
        return QRect(
            QPoint(
                int(x0 * self.page.canvas_width),
                int(y0 * self.page.canvas_height),
            ),
            QPoint(
                int(x1 * self.page.canvas_width),
                int(y1 * self.page.canvas_height),
            ),
        )

    def paintEvent(self, e):
        if not self.active:
            return
        painter = QPainter(self)
        rect = QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, QColor("#4499cccc"))

    def enterEvent(self, e):
        self.active = True
        self.update()

    def leaveEvent(self, e):
        self.active = False
        self.update()

    def mousePressEvent(self, e):
        self.handle_link(*self.link_data)

    def handle_link(self, *link_data):
        pass

########################################################################
# ExternalLink
########################################################################

class ExternalLink(DocLink):

    def handle_link(self, url):
        QDesktopServices.openUrl(QUrl(url))

########################################################################
# InternalLink
########################################################################

class InternalLink(DocLink):

    def handle_link(self, target_page_num, x, y):
        try:
            target_page = self.page.document_view.pages[target_page_num]
        except:
            return
        else:
            target_page.go_to_internal_location(x, y)

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
        self.page_ratio = 2*11/8.5
        self.base_canvas_width = 1100
        self.internal_width = self.base_canvas_width
        self.internal_height = self.page_ratio * self.base_canvas_width
        self.zoom = 1.
        self.crop = 0.
        self.links = []
        self.found_items = []
        self.sel_start = None
        self.sel_rect = None
        self.last_search = ""
        self.page_loaded = False
        self._init_page_()
        self.recompute_size(False)

    def _init_page_(self):
        pass

    def set_zoom(self, new_zoom):
        if self.zoom != new_zoom:
            self.zoom = new_zoom
            self.recompute_size()

    def set_crop(self, new_crop):
        if self.crop != new_crop:
            self.crop = new_crop

    def recompute_size(self, preserve_relative_position=True):
        if self.document_view.last_scroll_delta >= 0:
            preserve_relative_position = False
        if preserve_relative_position:
            s0 = self.document_view.verticalScrollBar().value()
            h0 = self.canvas_height
            y = self.pos().y()
            r = s0 - y - h0
        self.canvas_width = int(self.base_canvas_width * self.zoom)
        self.canvas_height = int(self.base_canvas_width * self.page_ratio * self.zoom)
        self.setFixedSize(self.canvas_width, self.canvas_height)
        for l in self.links:
            l.recompute_size()
        for it in self.found_items:
            it.recompute_size()
        if preserve_relative_position:
            if (h1 := self.canvas_height) != h0:
                s1 = y + h1 + r
                self.document_view.verticalScrollBar().setValue(s1)

    def get_image(self):
        try:
            img = self.document.get_image(self.page_num, self.zoom, self.crop)
        except KeyError:
            img = self.generate_image()
            self.document.save_image(self.page_num, self.zoom, img, self.crop)
        return img

    def generate_image(self):
        return None

    def paintEvent(self, e):
        if not self.page_loaded:
            self._load_page()
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform
        )
        rect = QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, Qt.white)
        self.paint_page(painter, rect)
        painter.drawRect(rect)
        if self.sel_rect is not None:
            pen = QPen(QColor("#0000ff"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.fillRect(self.sel_rect, QColor("#44ffcc00"))
            painter.drawRect(self.sel_rect)

    def paint_page(self, painter, rect):
        img = self.get_image()
        if img is not None:
            painter.drawImage(rect,img)

    def _load_page(self):
        self.load_page()
        self.load_links()
        for l in self.links:
            l.show()
        self.recompute_size()
        self.page_loaded = True

    def load_page(self):
        label = QLabel(f"# {self.page_num+1}/{self.document.num_pages}", parent=self)
        label.move(3,3)
        label.show()

    def load_links(self):
        return

    def go_to_internal_location(self, int_x, int_y):
        if not self.page_loaded:
            self._load_page()
        dy = int_y / self.internal_height * self.canvas_height / self.zoom
        self.document_view.go_to(self.page_num, dy)

    def _find(self, needle = ""):
        if self.last_search == needle:
            return
        if not self.page_loaded:
            self._load_page()
        self.clear_found_items()
        if needle != "":
            self.find(needle)
            for it in self.found_items:
                it.show()
            self.last_search = needle
        self.recompute_size()

    def clear_found_items(self):
        for it in self.found_items:
            it.setParent(None)
        self.found_items = []
        self.last_search = ""

    def find(self, needle):
        pass

    def mousePressEvent(self, event):
        self.sel_start = event.pos()
        self.sel_rect = None
        self.update()

    def mouseMoveEvent(self, event):
        self.sel_rect = QRect(self.sel_start, event.pos())
        self.update()
    
    def mouseReleaseEvent(self, event):
        self._copy_selection()

    def _copy_selection(self):
        if self.sel_rect is None:
            return
        r = self.sel_rect.normalized()
        x0, y0, x1, y1 = r.getCoords()
        internal_rect = (
            x0 / self.canvas_width * self.internal_width,
            y0 / self.canvas_height * self.internal_height,
            x1 / self.canvas_width * self.internal_width,
            y1 / self.canvas_height * self.internal_height,
        )
        if __debug__: deb(copy_selection=internal_rect)
        sel = self.copy_selection(internal_rect)
        if sel:
            can_sel = unicodedata.normalize('NFKD',sel)
            if __debug__: deb(new_clipboard=repr(can_sel))
            qapp = QCoreApplication.instance()
            cb = qapp.clipboard()
            cb.setText(can_sel)

    def copy_selection(self, rect):
        pass

########################################################################
# EmptyDocucment
########################################################################

class EmptyDocucment:

    page_class = EmptyPage
    doc_type = "Unknown"
    cache_size_limit = 20

    def __init__(self, file_name):
        self.file_name = file_name
        self.images = {}
        self.num_pages = 0
        self.toc = []
        self._init_document_()

    def _init_document_(self):
        self.num_pages = 47

    def save_image(self, page_num, zoom, img, crop=0):
        while len(self.images) > self.cache_size_limit:
            k = next(iter(self.images))
            self.images.pop(k)
        self.images[page_num, zoom, crop] = img

    def get_image(self, page_num, zoom, crop=0):
        return self.images[page_num, zoom, crop]

########################################################################
# DocumentView
########################################################################

class DocumentView(QScrollArea):

    document_class = EmptyDocucment

    def __init__(self, file_name, *args, **kws):
        super().__init__(*args, **kws)
        self.file_name = file_name
        if __debug__: deb(file_name=file_name)
        self.gap = gap = 12
        self.history = [(0,-1.0*gap)]
        self.history_pos = 0
        self.zoom = 1.
        self.crop = 0.
        self._init_document_()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.horizontalScrollBar().installEventFilter(self.hbar_filter)
        self.setAlignment(Qt.AlignCenter)
        self.container = container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(gap, gap, gap, gap)
        self.layout.setSpacing(gap)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        container.setLayout(self.layout)
        self.stack = QStackedWidget()
        self.stack.installEventFilter(self.stack_paint_filter)
        self.page_mode = "continuous"
        self.setWidget(container)
        self._y = 0
        self.last_scroll_delta = 0
        self.verticalScrollBar().valueChanged.connect(self.record_scroll)
        self.last_search = ""
        self.current_found_item = None
        self._init_pages_()

    @event_filter
    def hbar_filter(obj, event):
        if event.type() != QEvent.Wheel:
            return False
        elif event.modifiers() == Qt.NoModifier:
            return True
        else:
            return False

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

    def single_page_mode(self):
        if self.page_mode == "single":
            return
        n = self.current_page_number
        for p in reversed(self.pages):
            self.layout.removeWidget(p)
        self.layout.addWidget(self.stack)
        for p in self.pages:
            self.stack.addWidget(p)
        self.stack.show()
        self.stack.setCurrentIndex(n)
        self.page_mode = "single"

    def continuous_page_mode(self):
        if self.page_mode == "continuous":
            return
        n = self.stack.currentIndex()
        for p in reversed(self.pages):
            self.stack.removeWidget(p)
        self.layout.removeWidget(self.stack)
        for p in self.pages:
            self.layout.addWidget(p)
            p.show()
        self.go_to(n)
        self.page_mode = "continuous"

    @event_filter
    def stack_paint_filter(obj, event):
        if event.type() == QEvent.Paint:
            page = obj.currentWidget()
            if page:
                if not page.page_loaded:
                    page.load_page()
                obj.setFixedSize(page.canvas_width, page.canvas_height)
        return False

    def record_scroll(self, new_y):
        self.last_scroll_delta = new_y - self._y
        self._y = new_y

    def keyPressEvent(self, e):
        k = e.key()
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            if k == Qt.Key_Minus:
                return self.crop_out()
            if k == Qt.Key_Equal:
                return self.crop_in()
            if k == Qt.Key_0:
                return self.reset_crop()
        else:
            if k == Qt.Key_Minus:
                return self.zoom_out()
            if k == Qt.Key_Equal:
                return self.zoom_in()
            if k == Qt.Key_0:
                return self.reset_zoom()
        if self.page_mode == "continuous":
            if k == Qt.Key_S:
                return self.single_page_mode()
            if k == Qt.Key_G:
                return self.go_to_page_dialog()
            if k == Qt.Key_F:
                return self.find_dialog()
            if k == Qt.Key_N:
                return self.find_next()
            if k == Qt.Key_M:
                return self.find_previous()
            if k == Qt.Key_BracketLeft:
                return self.go_back()
            if k == Qt.Key_BracketRight:
                return self.go_forward()
        if self.page_mode == "single":
            if k == Qt.Key_C:
                return self.continuous_page_mode()
            if k in (
                Qt.Key_Space,
                Qt.Key_Enter,
                Qt.Key_Right,
                Qt.Key_Down,
            ):
                return self.spm_next_page()
            if k in (
                Qt.Key_Left,
                Qt.Key_Up,
            ):
                return self.spm_previous_page()
        super().keyPressEvent(e)

    def spm_next_page(self):
        n = self.stack.currentIndex() + 1
        if n >= len(self.pages):
            return
        self.stack.setCurrentIndex(n)

    def spm_previous_page(self):
        n = self.stack.currentIndex() - 1
        if n < 0:
            return
        self.stack.setCurrentIndex(n)

    def zoom_out(self):
        self.set_zoom(zoom_delta=-0.1)
        return
        if self.zoom > 0.5:
            self.zoom -= 0.1
            self.zoom_pages()

    def zoom_in(self):
        self.set_zoom(zoom_delta=0.1)
        return
        if self.zoom < 5:
            self.zoom += 0.1
            self.zoom_pages()

    def reset_zoom(self):
        self.set_zoom(new_zoom=1.)
        return
        if self.zoom != 1.:
            self.zoom = 1.
            self.zoom_pages()

    def set_zoom(self, new_zoom=None, zoom_delta=0.):
        if new_zoom is None:
            new_zoom = self.zoom + zoom_delta
        if not (0.5 <= new_zoom <= 5):
            return
        if new_zoom == self.zoom:
            return
        n, dy = self.get_current_rel_pos(window_point="center")
        h = self.get_current_rel_h_scroll()
        self.zoom = new_zoom
        for p in self.pages:
            p.set_zoom(self.zoom)
        def _for_later():
            self.go_to(n, dy, save_current_position=False, window_point="center")
            self.set_rel_h_scroll(h)
        QTimer.singleShot(0, _for_later)

    def crop_out(self):
        self.set_crop(crop_delta=-0.025)

    def crop_in(self):
        self.set_crop(crop_delta=0.025)

    def reset_crop(self):
        self.set_crop(new_crop=0.)

    def set_crop(self, new_crop=None, crop_delta=0.):
        if new_crop is None:
            new_crop = self.crop + crop_delta
        if not (0. <= new_crop <= 0.3):
            return
        if new_crop == self.crop:
            return
        self.crop = new_crop
        for p in self.pages:
            p.set_crop(new_crop)
            if not p.visibleRegion().isEmpty():
                p.update()

    @property
    def current_page_number(self):
        for page_num, page in enumerate(self.pages):
            if not page.visibleRegion().isEmpty():
                return page_num
        return 0

    def go_to_page_dialog(self):
        self.releaseKeyboard()
        cur_page_num = self.current_page_number
        new_page_num, ok = QInputDialog.getInt(
            self,
            "Go to page",
            "Go to page",
            value=cur_page_num+1,
            min=1,
            max=self.document.num_pages,
            flags=Qt.Sheet,
        )
        self.grabKeyboard()
        if ok:
            new_page_num -= 1
            if new_page_num != cur_page_num:
                self.go_to(new_page_num)

    def get_current_rel_h_scroll(self):
        x = self.horizontalScrollBar().value()
        m = self.horizontalScrollBar().maximum()
        if not m:
            return 0.5
        return x/m

    def set_rel_h_scroll(self, r):
        m = self.horizontalScrollBar().maximum()
        self.horizontalScrollBar().setValue(int(r*m))

    def get_current_rel_pos(self, window_point="north"):
        y = self.verticalScrollBar().value()
        if window_point == "north":
            pass
        elif window_point == "center":
            h = self.verticalScrollBar().pageStep()
            y += int(h/2)
        elif window_point == "south":
            h = self.verticalScrollBar().pageStep()
            y += h
        else:
            pass
        for page_num, page in enumerate(self.pages):
            b = page.geometry().bottom()
            if y <= b:
                break
        dy = (y-page.y())/self.zoom
        return page_num, dy


    def go_to(
            self,
            page_num=None,
            dy=None,
            save_current_position=True,
            window_point="north",
    ):
        pos0 = self.get_current_rel_pos(window_point)
        if dy is None:
            dy = -self.gap/self.zoom
        pos = page_num, dy
        if pos0 == pos:
            return
        try:
            page = self.pages[page_num]
        except:
            return
        if save_current_position:
            if pos0 != self.history[self.history_pos]:
                self.history_pos += 1
                self.history[self.history_pos:] = [pos0]
            self.history_pos += 1
            self.history[self.history_pos:] = [pos]
        if not page.page_loaded:
            page._load_page()
        y = page.pos().y()
        if window_point == "north":
            v = int(y + dy * self.zoom)
        elif window_point == "center":
            h = self.verticalScrollBar().pageStep()
            v = int(y + dy * self.zoom) - int(h/2)
        elif window_point == "south":
            h = self.verticalScrollBar().pageStep()
            v = int(y + dy * self.zoom) - h
        else:
            v = int(y + dy * self.zoom)
        self.verticalScrollBar().setValue(v)
        pos0 = self.get_current_rel_pos(window_point)

    def go_back(self):
        if self.history_pos > 0:
            self.history_pos -= 1
            n, y = self.history[self.history_pos]
            self.go_to(n, y, save_current_position=False)

    def go_forward(self):
        if self.history_pos < len(self.history)-1:
            self.history_pos += 1
            n, y = self.history[self.history_pos]
            self.go_to(n, y, save_current_position=False)

    def find_dialog(self):
        self.releaseKeyboard()
        needle, ok = QInputDialog.getText(
            self,
            "Find",
            "Find:",
            text=self.last_search,
            flags=Qt.Sheet,
        )
        self.grabKeyboard()
        if ok:
            self.last_search = needle
            self.find_first(needle)

    def find_first(self, needle):
        p = p0 = self.current_page_number
        while True:
            page = self.pages[p]
            page._find(needle)
            if page.found_items:
                break
            p += 1
            if p >= len(self.pages):
                p = 0
            if p == p0:
                self.current_found_item = None
                return
        it = page.found_items[0]
        self.current_found_item = it
        it.trigger_next_page_find()
        it.active = True
        self.ensureWidgetVisible(it)
        it.page.update()

    def find_next(self):
        if (it := self.current_found_item):
            n = it.next()
            self.current_found_item = n
            it.active = False
            n.active = True
            def _for_later():
                self.ensureWidgetVisible(n)
                n.page.update()
            QTimer.singleShot(0, _for_later)

    def find_previous(self):
        if (it := self.current_found_item):
            n = it.previous()
            self.current_found_item = n
            it.active = False
            n.active = True
            def _for_later():
                self.ensureWidgetVisible(n)
                n.page.update()
            QTimer.singleShot(0, _for_later)

########################################################################
# PdfPage
########################################################################

class PdfPage(EmptyPage):

    def load_page(self):
        self.pdf_page = self.document.pdfdoc[self.page_num]
        self.display_list = d = self.pdf_page.getDisplayList()
        self.internal_height = d.rect.height
        self.internal_width = d.rect.width
        self.page_ratio = d.rect.height / d.rect.width
        self.text_page = None
        self.page_words = None

    def generate_image(self):
        hcrop = int(self.crop*self.internal_width)
        vcrop = int(self.crop*self.internal_height)
        crop_rect = fitz.IRect(
            hcrop,
            vcrop,
            self.internal_width - hcrop,
            self.internal_height - vcrop
        )
        r = 2*self.canvas_width / (self.internal_width - 2*hcrop)
        m = fitz.Matrix(r, r)
        pix = self.display_list.getPixmap(matrix=m, clip=crop_rect)
        fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        return img

    def load_links(self):
        for link in self.pdf_page.links():
            k = link['kind']
            if k == fitz.LINK_GOTO:
                if (target_page_num := link['page']) == -1:
                    continue
                link_class = InternalLink
                target_point = link['to']
                link_data = (target_page_num, target_point.x, target_point.y)
            elif k == fitz.LINK_URI:
                link_class = ExternalLink
                link_data = (link['uri'],)
            else:
                continue
            r = link['from']
            rel_rect = (
                r.x0 / self.display_list.rect.width,
                r.y0 / self.display_list.rect.height,
                r.x1 / self.display_list.rect.width,
                r.y1 / self.display_list.rect.height,
            )
            self.links.append(link_class(self, rel_rect, *link_data))

    def find(self, needle):
        if self.text_page is None:
            self.text_page = self.display_list.getTextPage()
        rlist = self.text_page.search(needle, quads=False) 
        for r in rlist:
            rel_rect = (
                r.x0 / self.display_list.rect.width,
                r.y0 / self.display_list.rect.height,
                r.x1 / self.display_list.rect.width,
                r.y1 / self.display_list.rect.height,
            )
            self.found_items.append(FoundText(needle, self, rel_rect))

    def copy_selection(self, rect):
        if self.text_page is None:
            self.text_page = self.display_list.getTextPage()
        if self.page_words is None:
            words = []
            self.text_page.extractWORDS(words)
            words.sort(key=lambda w: (w[3], w[0]))
            self.page_words = words
        frect = fitz.Rect(*rect)
        words = [
            w
            for w in self.page_words
            if fitz.Rect(w[:4]) in frect
        ]
        group = itertools.groupby(words, key=lambda w: w[3])
        sel = "\n".join([
            " ".join(w[4] for w in gwords)
            for y1, gwords in group
        ])
        return sel
        for y1, gwords in group:
            print(" ".join(w[4] for w in gwords))


########################################################################
# PdfDocument
########################################################################

class PdfDocument(EmptyDocucment):

    page_class = PdfPage
    doc_type = "PDF"

    def _init_document_(self):
        self.pdfdoc = fitz.open(self.file_name)
        self.num_pages = self.pdfdoc.pageCount
        raw_toc = self.pdfdoc.getToC()
        self.toc = [
            [
                f"{'    '*(lvl-1)}{title} (p.{page_num})", 
                page_num
            ]
            for lvl, title, page_num in raw_toc
            if 0 <= page_num < self.num_pages
        ]

########################################################################
# PdfView
########################################################################

class PdfView(DocumentView):
    document_class = PdfDocument

########################################################################
# DjvuPage
########################################################################

class DjvuPage(EmptyPage):

    def load_page(self):
        self.djvupage = p = self.document.djvudoc.pages[self.page_num]
        pj = p.decode(wait = True)
        self.internal_height = pj.height
        self.internal_width = pj.width
        self.page_ratio = pj.height / pj.width
        self.recompute_size()
        self.djvupagejob = pj

    def generate_image(self):
        dpf = djvud.PixelFormatRgbMask(0xFF0000, 0xFF00, 0xFF, 0xFF000000, bpp=32)
        dpf.rows_top_to_bottom = 1
        dpf.y_top_to_bottom = 0
        pj = self.djvupagejob
        hcrop = int(self.crop*self.canvas_width)
        vcrop = int(self.crop*self.canvas_height)
        data = pj.render(
            djvud.RENDER_COLOR,
            (0, 0, self.canvas_width+2*hcrop, self.canvas_height+2*vcrop),
            (hcrop, vcrop, self.canvas_width, self.canvas_height),
            # (0, 0, self.canvas_width, self.canvas_height),
            # (0, 0, self.canvas_width, self.canvas_height),
            dpf,
        )
        img = QImage(data, self.canvas_width, self.canvas_height, QImage.Format_RGB32)
        return img

    def load_links(self):
        an = self.djvupage.annotations
        an.wait()
        for se in an.sexpr.value:
            if len(se) >= 4 and se[0] == djvue.Symbol("maparea"):
                data = (se[1],)
                x0, y0, w, h = se[3][1:]
                rect = (
                    x0 / self.internal_width, 
                    1 - (y0+h) / self.internal_height,
                    (x0+w) / self.internal_width, 
                    1 - y0 / self.internal_height, 
                )
                self.links.append(ExternalLink(self, rect, *data))

########################################################################
# DjvuDocument
########################################################################

class DjvuDocument(EmptyDocucment):

    page_class = DjvuPage
    doc_type = "DjVu"

    def _init_document_(self):
        ctx = djvud.Context()
        uri = djvud.FileURI(self.file_name)
        self.djvudoc = doc = ctx.new_document(uri)
        doc.decoding_job.wait()
        self.num_pages = len(doc.pages)

    def _unused_get_toc_(self):
        outline = doc.outline
        outline.wait()
        print(outline.sexpr)
        for se in outline.sexpr.value:
            print(se)

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
        self.update_menu(view)

    def remove_current_tab(self):
        row = self.currentRow()
        if row == -1:
            return
        it = self.takeItem(row)
        view = it.data(self._data_key)
        view.releaseKeyboard()
        self.stack.removeWidget(view)
        new_view = self.stack.currentWidget()
        if new_view:
            new_view.grabKeyboard()
        self.update_menu(new_view)
        del it

    def on_click(self, it):
        view = it.data(self._data_key)
        old_view = self.stack.currentWidget()
        if old_view:
            old_view.releaseKeyboard()
        self.stack.setCurrentWidget(view)
        view.grabKeyboard()
        self.update_menu(view)

    def update_menu(self, view):
        self.viewer.set_page_menu(view)


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

    def _init_main_menu_(self):
        self.menubar = QMenuBar()
        self.main_menu = self.menubar.addMenu("ollo")
        self.menu_actions = []
        for title, key, handler, role in (
            ["About ollo", None, None, None],
            ["separator", None, None, None],
            ["Close", QKeySequence.Close, self.close_view, None],
            ["Duplicate", QKeySequence(Qt.CTRL + Qt.Key_D), self.duplicate_view, None],
            ["separator", None, None, None],
            ["Single page mode", QKeySequence(Qt.Key_S), None, None],
            ["Continuous page mode", QKeySequence(Qt.Key_C), None, None],
            ["separator", None, None, None],
            ["Zoom in", QKeySequence(Qt.Key_Plus), None, None],
            ["Zoom out", QKeySequence(Qt.Key_Minus), None, None],
            ["Crop in", QKeySequence(Qt.META + Qt.Key_Plus), None, None],
            ["Crop out", QKeySequence(Qt.META + Qt.Key_Minus), None, None],
            ["separator", None, None, None],
            ["Go to page", QKeySequence(Qt.Key_G), None, None],
            ["Find...", QKeySequence(Qt.Key_F), None, None],
            ["Quit", None, self.quit_dialog, QAction.QuitRole],
        ):
            act = QAction(title)
            if title == "separator":
                act.setSeparator(True)
            if role is None:
                act.setMenuRole(QAction.ApplicationSpecificRole)
            else:
                act.setMenuRole(role)
            if key is not None:
                act.setShortcuts(key)
            if handler is not None:
                act.triggered.connect(handler)
            self.menu_actions.append(act)
            self.main_menu.addAction(act)

    def _init_page_menu_(self):
        self.page_menu = self.menubar.addMenu("0 pages")
        self.no_file_action = QAction("No file open")
        self.page_menu.addAction(self.no_file_action)
        self.page_menu_title_template = ""
        self.page_menu_timer = QTimer()
        self.page_menu_timer.timeout.connect(self.update_page_menu)
        self.page_menu_timer.start(500)

    def set_page_menu(self, view=None):
        self.page_actions = []
        m = self.page_menu
        m.clear()
        if view is None:
            num_pages = 0
            toc = None
            doc_type = ""
        else:
            num_pages = view.document.num_pages
            toc = view.document.toc
            doc_type = f"{view.document.doc_type} - "
        self.page_menu_title_template = \
            f"{doc_type}page {{}} of {num_pages}"
        if toc is None:
            return
        if not toc:
            toc = [["no table of contents", None]]
        for heading, page in toc:
            act = QAction(heading)
            if heading == "separator":
                act.setSeparator(True)
            if page is not None:
                def _handle(*a, page=page):
                    view.go_to(page-1)
                act.triggered.connect(_handle)
            m.addAction(act)
            self.page_actions.append(act)

    def update_page_menu(self):
        if not (current_view := self.stack.currentWidget()):
            return
        title = self.page_menu_title_template.format(
            current_view.current_page_number+1
        )
        self.page_menu.setTitle(title)

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
        return view

    def duplicate_view(self, *args):
        current_view = self.stack.currentWidget()
        file = current_view.file_name
        view = self.add_view(file)
        view.zoom = current_view.zoom
        if view.zoom != 1.:
            for p in view.pages:
                p.set_zoom(view.zoom)
        view.history = current_view.history
        view.history_pos = current_view.history_pos
        n, dy = current_view.get_current_rel_pos()
        r = current_view.get_current_rel_h_scroll()
        def _for_later():
            view.go_to(n, dy, save_current_position=False)
            view.set_rel_h_scroll(r)
        QTimer.singleShot(0, _for_later)

    def quit_dialog(self, *args):
        current_view = self.stack.currentWidget()
        if current_view is None:
            self.qapp.quit()
            return
        current_view.releaseKeyboard()
        msg = QMessageBox(self)
        msg.setWindowFlags(Qt.Sheet)
        msg.setText("Are you sure?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        for b in msg.buttons():
            b.setFocusPolicy(Qt.StrongFocus)
        reply = msg.exec()
        current_view.grabKeyboard()
        if reply == QMessageBox.Yes:
            self.qapp.quit()

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
        fitz.TOOLS.set_aa_level(8)
        if __debug__: deb(AA=fitz.TOOLS.show_aa_level())
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

