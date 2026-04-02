from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMainWindow,
    QTextEdit, QLineEdit, QPushButton, QHBoxLayout,
    QListWidget, QSplitter, QListWidgetItem
)
from PySide6.QtGui import QTextCursor
from app.controller import BrainCellController
from PySide6.QtCore import QThread, Signal, QObject, QTimer
import sys
import markdown
from utils.chat_storage import save_chat, load_chats
import json
from datetime import datetime
import re
from latex2mathml.converter import convert as latex_to_mathml


class LLMWorker(QObject):
    token = Signal(str)
    finished = Signal()

    def __init__(self, controller, history):
        super().__init__()
        self.controller = controller
        self.history = history

    def run(self):
        self.controller.run(
            self.history,
            self.token.emit,
            self.finished.emit
        )


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chat_title = None
        self.controller = BrainCellController()
        self.is_running = False
        self.current_response = ""
        self.chat_history = []
        self.chat_filename = None

        self.thinking = False
        self.thinking_timer = QTimer()
        self.thinking_state = 0
        self.thinking_timer.timeout.connect(self.update_thinking)

        self.setWindowTitle("BrainCell Desktop")
        self.resize(1000, 800)

        # Menu bar
        self.menu = self.menuBar()
        file_menu = self.menu.addMenu("Chat")
        
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.clicked.connect(self.new_chat)

        main_layout = QVBoxLayout()

        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_chat)
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)

        self.input_box = QLineEdit()
        self.send_button = QPushButton("Send")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.new_chat_button)
        left_layout.addWidget(self.chat_list)
        left_panel = QWidget()
        left_panel.setLayout(left_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.chat_area)
        right_layout.addLayout(input_layout)
        right_panel.setLayout(right_layout)

        splitter = QSplitter()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 800])
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.apply_theme()

        # UI logic
        self.send_button.clicked.connect(self.handle_send)
        self.input_box.returnPressed.connect(self.handle_send)
        self.input_box.setPlaceholderText("Ask BrainCell...")
        self.refresh_chat_list()

    def refresh_chat_list(self):
        self.chat_list.clear()
        chats = load_chats()
        for file in chats:
            path = f"chats/{file}"
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    title = data.get("title", file)
            except:
                title = file
            item = QListWidgetItem(title)
            item.setData(1, file)
            self.chat_list.addItem(item)

    def render_markdown(self, text):
        def repl(match):
            latex = match.group(1)
            try:
                return latex_to_mathml(latex)
            except:
                return latex
        text = re.sub(r"\$(.*?)\$", repl, text)
        return markdown.markdown(
            text,
            extensions=[
                "fenced_code",
                "tables",
                "pymdownx.superfences",
                "pymdownx.highlight"
            ]
        )
    
    def load_chat(self, item):
        filename = item.data(1)
        path = f"chats/{filename}"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.chat_history = data["messages"]
        self.chat_title = data["title"]
        self.chat_filename = filename

        self.chat_area.clear()
        for msg in self.chat_history:
            if msg["role"] == "user":
                self.chat_area.append(f"<br><b>You:</b> {msg['content']}")
            else:
                html = self.render_markdown(msg["content"]).replace("<p>", "").replace("</p>", "")
                self.chat_area.insertHtml(f"<br><br><span style='color:#2f9e44'><b>BrainCell:</b> {html}</span>")
                
    def new_chat(self):
        self.chat_area.clear()
        self.chat_history = []
        self.chat_filename = None
        self.chat_title = None

    def apply_theme(self):
        with open("ui/style.qss", "r") as f:
            self.setStyleSheet(f.read())

    def handle_send(self):
        if self.is_running:
            return

        message = self.input_box.text().strip()
        if not message:
            return
        if self.chat_filename is None:
            self.chat_filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
            self.chat_title = message[:40]
        self.chat_area.append(f"<br><b>You:</b> {message}")
        self.chat_history.append({"role": "user", "content": message})
        self.input_box.clear()
        
        self.start_response()
        self.chat_area.append("<span style='color:#f08c00'>Thinking</span>")
        self.thinking = True
        self.thinking_timer.start(400)

        self.thread = QThread()
        self.worker = LLMWorker(self.controller, self.chat_history)

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.token.connect(self.stream_token)
        self.worker.finished.connect(self.end_response)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def update_thinking(self):
        dots = ["", ".", "..", "..."]

        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.removeSelectedText()

        cursor.insertHtml(
            f"<span style='color:#f08c00'>Thinking{dots[self.thinking_state]}</span>"
        )
        self.thinking_state = (self.thinking_state + 1) % 4

    def stream_token(self, token):
        if self.thinking:
            self.thinking = False
            self.thinking_timer.stop()

            cursor = self.chat_area.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
            self.chat_area.insertHtml("<br><span style='color:#2f9e44'><b>BrainCell:</b> </span>")

        self.current_response += token
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(token)                #green response text. correct. should be printed. If you can, just save this itself with the green colour and span styling
        self.scroll_to_bottom()

    def start_response(self):
        self.is_running = True
        self.input_box.setDisabled(True)
        self.send_button.setText("Stop")
        
        self.send_button.clicked.disconnect()
        self.send_button.clicked.connect(self.stop_response)

    def end_response(self):
        self.is_running = False
        self.input_box.setDisabled(False)

        self.send_button.setText("Send")
        self.send_button.clicked.disconnect()
        self.send_button.clicked.connect(self.handle_send)

        response_md = self.current_response.strip()

        self.chat_history.append({
            "role": "assistant",
            "content": response_md
        })

        save_chat(self.chat_history, self.chat_filename, self.chat_title)
        self.refresh_chat_list()

        self.current_response = ""

    def stop_response(self):
        self.controller.stop()
        if hasattr(self, "thread"):
            self.thread.quit()
            self.thread.wait()
        self.chat_area.append("<span style='color:#f08c00'><b>Stopped.</b></span>")
        self.end_response()

    def scroll_to_bottom(self):
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

def launch_app():
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())