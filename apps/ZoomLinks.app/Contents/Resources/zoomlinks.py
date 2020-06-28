
link_list = [
    [
        "Office Hours",
        "475 653 618",
        "officehour",
        "https://oklahoma.zoom.us/j/475653618?pwd=cGpreUNhNGNSMklxSnVsUFU0SFQ2dz09",
    ],
    [
        "AG Reading Course",
        "139 716 655",
        "386420",
        "https://oklahoma.zoom.us/j/139716655?pwd=YzdhQTdGZ1cyZHd5RVcvZVBDNTdsdz09",
    ],
    [
        "Antonio",
        "957 4051 0020",
        "flags",
        "https://oklahoma.zoom.us/j/95740510020?pwd=L0k5aEhITElLRzhxTERmSUpSdi9hdz09",
    ],
    [
        "Daniel",
        "580 909 150",
        "887013",
        "https://oklahoma.zoom.us/j/580909150",
    ],
    [
        "Greg",
        "947 3806 4397",
        "11535339",
        "https://oklahoma.zoom.us/j/94738064397?pwd=OGdLSm4vNTJJMG5ERVBFSU5wdkt6QT09",
    ],
    [
        "Kazumi",
        "749 619 5513",
        "jing",
        "https://us02web.zoom.us/j/7496195513",
    ],
    [
        "Tommaso",
        "932 2193 5507",
        "conjecture",
        "https://oklahoma.zoom.us/j/93221935507?pwd=V3ltSVJZWHFveTNQWDBKRzJDQlpDQT09",
    ],
    [
        "Tommaso and Gebhard",
        "920 594 165",
        "nash",
        "https://utah.zoom.us/j/920594165",
    ],
]

########################################################################

import os
import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

########################################################################

css = """

    html {
        overflow : hidden;
        height   : 100%;
        margin   : 0px;
        padding  : 0px;
    }

    body {
        color   : black;
        margin  : 0px;
        padding : 0px;
        font-family: "Lucida Sans Unicode", "Lucida Grande", sans-serif;
        font-size: 10pt;
    }

    img {
        float: right;
        margin-top: 7.5px;
        padding-right: 10px;
        height : 22px;
        width : 22px;
    }

    h3 {
        height: 37px;
        line-height: 37px;
        margin: 0px;
        padding: 0px;
        padding-left: 10px;
    }

    .link_block {
        display: block;
        background: white;
        height : 32px;
        line-height: 32px;
    }

    .link_block:hover {
        background: transparent;
    }

    .link_block a {
        display: inline-block;
        text-decoration: none;
        color: inherit;
    }

    .link_block .title {
        padding-left:  10px;
        width: 220px;
    }

    .link_block .meeting_id {
        width: 120px;
    }

    .link_block .password {
        padding-right: 8px;
        text-align: right;
        width: 92px;
    }

    #message_box {
        position: fixed;
        bottom: 0;
        right: 10px;
        width: 100%;
        height: 27px;
        text-align: right;
        line-height: 27px;
        font-size: smaller;
    }

"""

########################################################################

js = """

function show_message(txt) {
    let box = document.getElementById("message_box");
    box.innerHTML = txt;
    return true;
}

"""

########################################################################

title = """

    <div id="message_box">Select a link</div>
    <img
        src="https://www.nicepng.com/png/full/1008-10087079_zoom-icon-zoom-video-conferencing-logo.png"
    >
    <h3>Zoom Links</h3>

"""

########################################################################

link_template = """

    <div class="link_block"
        ><a
            class="title"
            href="{url}"
            onclick="show_message('Opened meeting with ID {meeting_id}')"
            >{title}</span
        ><a
            class="meeting_id"
            href="copy:{meeting_id}"
            onclick="show_message('Copied meeting ID ({meeting_id}) to clipboard')"
            >{meeting_id}</a
        ><a
            class="password"
            href="copy:{password}"
            onclick="show_message('Copied password ({password}) to clipboard')"
            >{password}</a
    ></div>

"""
 
########################################################################

zoom_url = "zoommtg://zoom.us/join?confno={meeting_id}&pwd={password}"

########################################################################

html = f"<style>{css}</style><script>{js}</script>{title}" + "".join([
    link_template.format(
        url = zoom_url.format(
            meeting_id=mid.replace(" ",""),
            password=p,
        ),
        title = t,
        meeting_id = mid,
        password = p,
    )
    for t, mid, p, url in link_list
])

########################################################################

class MyPage(QWebEnginePage):
    cmd = 'open -a zoom.us "{url}"'
    def acceptNavigationRequest(self, url, *args):
        scheme = url.scheme()
        if scheme == "data":
            return True
        elif scheme == "zoommtg":
            os.system(self.cmd.format(url=url.url()))
        elif scheme == "copy":
            cb = QGuiApplication.clipboard()
            text = url.path().replace(" ", "")
            cb.setText(text)
        elif scheme in ("http", "https"):
            QDesktopServices.openUrl(url)
        return False

########################################################################

def run():
    app = QApplication(sys.argv)
    window = QMainWindow()
    browser = QWebEngineView(window)
    page = MyPage(browser)
    page.setBackgroundColor(Qt.transparent)
    page.setHtml(html)
    page.loadFinished.connect(lambda *a: window.show())
    browser.setPage(page)
    height = 37 + 32 * len(link_list) + 27;
    window.setGeometry(100,100,450,height)
    window.setCentralWidget(browser)
    if False:
        dock = QDockWidget("devtools", window)
        devtools = QWebEngineView(dock)
        devtools.page().setInspectedPage(page)
        dock.setWidget(devtools)
        window.addDockWidget(Qt.RightDockWidgetArea, dock)
    ret = app.exec_()
    del window
    return ret
 
########################################################################

if __name__ == "__main__":
    sys.exit(run())
