import sys
import tempfile
from PyQt5.QtCore import Qt, QUrl, pyqtSlot, QObject
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout,
    QAction, QMenu, QTabWidget, QMessageBox, QListWidget, QDialog, QDialogButtonBox, QLabel
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel


class Bridge(QObject):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

    @pyqtSlot(str)
    def performSearch(self, query):
        if query:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            self.browser.setUrl(QUrl(search_url))


class HistoryDialog(QDialog):
    def __init__(self, history):
        super().__init__()
        self.setWindowTitle("Histórico de Navegação")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout()

        self.list = QListWidget()
        for item in history:
            self.list.addItem(item)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.close)

        layout.addWidget(QLabel("Histórico:"))
        layout.addWidget(self.list)
        layout.addWidget(self.button_box)
        self.setLayout(layout)


class BrowserTab(QWidget):
    def __init__(self, history, incognito=False):
        super().__init__()
        self.history = history
        self.incognito = incognito

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.browser = QWebEngineView()

        # Usar perfil anônimo se incognito
        if self.incognito:
            profile = QWebEngineProfile()
            profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
            profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
            page = QWebEnginePage(profile, self.browser)
            self.browser.setPage(page)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Escreve um URL ou pesquisa...")
        self.url_bar.setStyleSheet("""
            QLineEdit {
                background-color: #2e2e2e;
                border: 1px solid #444;
                color: white;
                padding: 6px;
                border-radius: 6px;
            }
        """)
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        # Botões de navegação
        self.home_btn = QPushButton("⌂")
        self.back_btn = QPushButton("⟵")
        self.forward_btn = QPushButton("⟶")
        self.reload_btn = QPushButton("⟳")

        for btn in [self.home_btn, self.back_btn, self.forward_btn, self.reload_btn]:
            btn.setFixedSize(40, 30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333;
                    color: white;
                    border: 1px solid #555;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #444;
                }
            """)

        self.home_btn.clicked.connect(self.set_homepage)
        self.back_btn.clicked.connect(self.browser.back)
        self.forward_btn.clicked.connect(self.browser.forward)
        self.reload_btn.clicked.connect(self.browser.reload)

        # Menu de configurações com ações
        self.settings_menu = QMenu()
        self.settings_menu.setStyleSheet("""
            QMenu {
                background-color: #2e2e2e;
                color: white;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #444;
            }
        """)

        new_tab_action = QAction("Nova Aba", self)
        new_tab_action.triggered.connect(lambda: self.parent().parent().new_tab())

        new_incognito_action = QAction("Nova Aba Anônima", self)
        new_incognito_action.triggered.connect(lambda: self.parent().parent().new_incognito_tab())

        zoom_in_action = QAction("Zoom +", self)
        zoom_in_action.triggered.connect(self.zoom_in)

        zoom_out_action = QAction("Zoom -", self)
        zoom_out_action.triggered.connect(self.zoom_out)

        history_action = QAction("Histórico", self)
        history_action.triggered.connect(self.show_history)

        help_action = QAction("Ajuda", self)
        help_action.triggered.connect(self.show_help)

        self.settings_menu.addAction(new_tab_action)
        self.settings_menu.addAction(new_incognito_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(zoom_in_action)
        self.settings_menu.addAction(zoom_out_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(history_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(help_action)

        # Botão configurações com "⋮"
        self.settings_btn = QPushButton("⋮")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QPushButton::menu-indicator { image: none; }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        self.settings_btn.setMenu(self.settings_menu)

        # Layout da barra de navegação (botões + url + configurações)
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(10)
        nav_bar.addWidget(self.home_btn)
        nav_bar.addWidget(self.back_btn)
        nav_bar.addWidget(self.forward_btn)
        nav_bar.addWidget(self.reload_btn)
        nav_bar.addWidget(self.url_bar)
        nav_bar.addWidget(self.settings_btn)

        self.layout.addLayout(nav_bar)
        self.layout.addWidget(self.browser)

        # Bridge para pesquisa na homepage local
        self.channel = QWebChannel()
        self.bridge = Bridge(self.browser)
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        self.browser.urlChanged.connect(self.update_url)
        self.browser.loadFinished.connect(self.add_to_history_if_needed)

        # Homepage temporária
        self.homepage_path = None
        self.set_homepage()

    def navigate_to_url(self):
        query = self.url_bar.text().strip()
        if query.startswith("http://") or query.startswith("https://"):
            self.browser.setUrl(QUrl(query))
        elif "." in query and " " not in query:
            self.browser.setUrl(QUrl("https://" + query))
        else:
            search_url = "https://www.google.com/search?q=" + query.replace(" ", "+")
            self.browser.setUrl(QUrl(search_url))

    def update_url(self, q):
        url_str = q.toString()
        if self.is_homepage_file(url_str):
            self.url_bar.setText("")
        else:
            self.url_bar.setText(url_str)

    def set_homepage(self):
        html = self.zypox_home_page()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
        temp_file.write(html)
        temp_file.close()
        self.homepage_path = temp_file.name
        self.browser.setUrl(QUrl.fromLocalFile(self.homepage_path))
        self.url_bar.setText("")

    def is_homepage_file(self, url_str):
        return self.homepage_path is not None and self.homepage_path in url_str

    def add_to_history_if_needed(self):
        url = self.browser.url().toString()
        if url.startswith("http") and not self.incognito:
            self.history.append(url)

    def zoom_in(self):
        self.browser.setZoomFactor(self.browser.zoomFactor() + 0.1)

    def zoom_out(self):
        self.browser.setZoomFactor(max(self.browser.zoomFactor() - 0.1, 0.1))

    def show_history(self):
        if self.incognito:
            QMessageBox.information(self, "Histórico", "Não há histórico disponível em modo anônimo.")
            return
        dialog = HistoryDialog(self.history)
        dialog.exec_()

    def show_help(self):
        QMessageBox.information(self, "Ajuda - Zypox",
                                "Zypox Browser\n\n"
                                "• Nova Aba - Abre uma nova aba\n"
                                "• Nova Aba Anônima - Abre aba privada\n"
                                "• Zoom + / - para aumentar ou reduzir\n"
                                "• Histórico - Ver páginas visitadas\n"
                                "• Pesquisa rápida na homepage")

    def zypox_home_page(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script>
                document.addEventListener("DOMContentLoaded", function () {
                    new QWebChannel(qt.webChannelTransport, function (channel) {
                        window.bridge = channel.objects.bridge;
                        const input = document.getElementById("search");
                        input.addEventListener("keydown", function (e) {
                            if (e.key === "Enter") {
                                let query = input.value.trim();
                                if (query) {
                                    bridge.performSearch(query);
                                }
                            }
                        });
                    });
                });
            </script>
            <style>
                body {
                    background-color: #1e1e1e;
                    color: white;
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin-top: 200px;
                }
                input {
                    padding: 15px;
                    width: 400px;
                    font-size: 18px;
                    border-radius: 10px;
                    border: none;
                }
                input:focus {
                    outline: none;
                    box-shadow: 0 0 10px #66f;
                }
            </style>
        </head>
        <body>
            <input id="search" type="text" placeholder="Pesquisa rápida com o Zypox...">
        </body>
        </html>
        """


class ZypoxBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zypox Browser")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        self.history = []

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.tabBarDoubleClicked.connect(self.new_tab)

        self.setCentralWidget(self.tabs)

        # Criar primeira aba padrão
        self.new_tab()

    def new_tab(self, index=None, incognito=False):
        tab = BrowserTab(self.history, incognito=incognito)
        i = self.tabs.addTab(tab, "Anônimo" if incognito else "Nova Aba")
        self.tabs.setCurrentIndex(i)

    def new_incognito_tab(self):
        self.new_tab(incognito=True)

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def current_tab(self):
        return self.tabs.currentWidget()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ZypoxBrowser()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()