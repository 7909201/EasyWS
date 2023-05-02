import os.path
import re
import copy

import PyQt6.uic.enum_map
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sys

import flowlayout

from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QWidget,
    QTextEdit,
    QLabel,
    QTextBrowser,
    QWidgetItem,
    QFrame,
    QStyle,
)
from PySide6.QtGui import (
    QColor,
    QFontMetrics,
    QFont,
)
from PySide6 import QtCore

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents']

# The ID of the Document To Edit
PRODUCT_DOC_ID = '1vm-_NeA4moitzrY51EL5wfbmAOjzV46M_I1Ec6k8O9c'
TEST_DOC_ID = "13XlqTA3vejwC9-3Il5w_188c5YeAlDXMOZHu6i9mEK0"


class Style:
    def __init__(self, data: dict, default_style=None):
        self.name = data.get("namedStyleType")
        self.bold = data["textStyle"].get("bold", False) or getattr(default_style, "bold", False)
        self.italic = data["textStyle"].get("italic", False) or getattr(default_style, "italic", False)
        self.underline = data["textStyle"].get("underline", False) or getattr(default_style, "underline", False)
        self.strikethrough = data["textStyle"].get("strikethrough", False) or getattr(default_style, "strikethrough",
                                                                                      False)

        self.background: (int, int, int) = data["textStyle"].get("backgroundColor")
        if self.background:
            self.background = (
                int(self.background["color"]["rgbColor"]["red"] * 255),
                int(self.background["color"]["rgbColor"]["green"] * 255),
                int(self.background["color"]["rgbColor"]["blue"] * 255))
        else:
            self.background = getattr(default_style, "background", None)

        self.foreground: (int, int, int) = data["textStyle"].get("foregroundColor")
        if self.foreground:
            self.foreground = self.foreground["color"].get("rgbColor")
        if self.foreground:
            self.foreground = (
                int(self.foreground.get("red", 0) * 255),
                int(self.foreground.get("green", 0) * 255),
                int(self.foreground.get("blue", 0) * 255))
        else:
            self.foreground = getattr(default_style, "foreground", None)

        try:
            # self.fontSize = data["textStyle"]["fontSize"]["magnitude"] * 72 // 96
            self.fontSize = data["textStyle"]["fontSize"]["magnitude"]
        except KeyError:
            self.fontSize = getattr(default_style, "fontSize", None)
        try:
            self.font = data["textStyle"]["weightedFontFamily"]["fontFamily"]
        except KeyError:
            self.font = getattr(default_style, "font", None)


class Chunk:
    def __init__(self, data: dict, default_style, newline: bool = False):
        self.start_index: int = data["startIndex"]
        self.end_index: int = data["endIndex"]
        self.raw_text: str = data["textRun"]["content"].replace("\n", "")
        self.style: Style = Style(data["textRun"], default_style)
        self.new_line: bool = newline
        # try:
        #     if data["textRun"]["textStyle"]:
        #         self.style: Style = Style(data["textRun"])
        #     else:
        #         self.style = default_style
        # except KeyError:
        #     self.style = default_style


class Document:
    def __init__(self, doc_id: str, service):
        data = service.documents().get(documentId=doc_id).execute()
        print(data)
        self.service = service

        self.id = data["documentId"]
        self.title = data["title"]
        self.body = data["body"]
        self.documentStyle = data["documentStyle"]
        self.named_styles = {x["namedStyleType"]: Style(x) for x in data["namedStyles"]["styles"]}

    def _insert_text(self, requests: list) -> None:
        print(requests)
        self.service.documents().batchUpdate(
            documentId=self.id,
            body={'requests': requests}).execute()

    def get_margins(self) -> tuple[int, int, int, int]:
        return (
            int(self.documentStyle["marginLeft"]["magnitude"] * (96 / 72)),
            int(self.documentStyle["marginTop"]["magnitude"] * (96 / 72)),
            int(self.documentStyle["marginRight"]["magnitude"] * (96 / 72)),
            int(self.documentStyle["marginBottom"]["magnitude"] * (96 / 72))
        )

    def get_chunks(self) -> list[Chunk]:
        chunks = []
        # Section Consists Mostly Of Lines Broken By `\n` But Also Includes Headers/Footers And Other Document Features
        for line in self.body["content"]:
            if "paragraph" in line.keys():
                # Chunk Represents A String Of Text That Has The Exact Same Formatting
                # A New Chunk Is Created When Formatting Such As Color, Font, And/Or Size Changes

                # The First Chunk Per Line Often Means That It Is A Newline
                # TODO: My Guess Is There Are Cases Where This Is Not True
                sub_chunks = []
                newline = True
                if line["paragraph"]["elements"][0].get("textRun"):
                    for text in re.split("(_+)", line["paragraph"]["elements"][0]["textRun"]["content"]):
                        print("Text: " + repr(text))
                        print("Content: " + repr(line["paragraph"]["elements"][0]["textRun"]["content"]))
                        print("Find: " + str(line["paragraph"]["elements"][0]["textRun"]["content"].find(text)))
                        sub_chunk = copy.deepcopy(line["paragraph"]["elements"][0])
                        sub_chunk["textRun"]["content"] = text
                        sub_chunk["startIndex"] = line["paragraph"]["elements"][0]["textRun"]["content"].find(text) + line["paragraph"]["elements"][0]["startIndex"]
                        sub_chunk["endIndex"] = line["paragraph"]["elements"][0]["textRun"]["content"].find(text) + len(text) + line["paragraph"]["elements"][0]["startIndex"]
                        sub_chunks.append(Chunk(sub_chunk, default_style=self.named_styles[
                            line["paragraph"]["paragraphStyle"]["namedStyleType"]], newline=newline))
                        newline = False

                    chunks.extend(sub_chunks)
                # chunks.append(Chunk(line["paragraph"]["elements"][0], default_style=self.named_styles[
                #     line["paragraph"]["paragraphStyle"]["namedStyleType"]], newline=True))
                for chunk in line["paragraph"]["elements"][1:]:
                    # chunks.append(Chunk(chunk, default_style=self.named_styles[
                    #      line["paragraph"]["paragraphStyle"]["namedStyleType"]]))
                    sub_chunks = []
                    if chunk.get("textRun"):
                        for text in re.split("(_+)", chunk["textRun"]["content"]):
                            sub_chunk = chunk
                            sub_chunk["textRun"]["content"] = text
                            sub_chunk["startIndex"] = chunk["textRun"]["content"].find(text) + chunk["startIndex"]
                            sub_chunk["endIndex"] = chunk["textRun"]["content"].find(text) + len(text) + chunk["startIndex"]
                            sub_chunks.append(Chunk(sub_chunk, default_style=self.named_styles[
                                line["paragraph"]["paragraphStyle"]["namedStyleType"]], newline=True))

                        chunks.extend(sub_chunks)

                    # split_newlines = chunk.split("\n")
                    # chunks.append(Chunk(split_newlines[0], default_style=self.named_styles[
                    #     line["paragraph"]["paragraphStyle"]["namedStyleType"]]))
                    # for subchunk in split_newlines[1: -1]:
                    #     chunks.append(Chunk(subchunk, default_style=self.named_styles[
                    #         line["paragraph"]["paragraphStyle"]["namedStyleType"]], newline=True))
                    # chunks.append(Chunk(split_newlines[-1], default_style=self.named_styles[
                    #     line["paragraph"]["paragraphStyle"]["namedStyleType"]]))
        print(chunks)
        return chunks

    def submit(self, wids):
        requests = []
        for wid in wids[::-1]:
            delete_tem = {'deleteContentRange':
                {'range':
                    {
                        'segmentId': '',
                        'startIndex': wid.chunk.start_index,
                        'endIndex': wid.chunk.end_index
                    }
                }}
            insert_tem = {'insertText':
                              {'location':
                                   {'index': wid.chunk.start_index},
                               'text': wid.toPlainText(),
                               },
                          }
            requests.append(delete_tem)
            requests.append(insert_tem)
        print(requests)
        self._insert_text(requests)


class Window(QWidget):
    def __init__(self, chunks: list[Chunk], named_styles, margins, doc):
        super().__init__()
        self.setWindowTitle("QGridLayout Example")
        # TODO: Make Background Color Of Document
        # Create a QGridLayout instance
        layout = flowlayout.FlowLayout(self, margins)
        # Add widgets to the layout
        for chunk in chunks:
            print(repr(chunk.raw_text), f"Start {chunk.start_index} End {chunk.end_index}")
            try:
                if "_" in chunk.raw_text:
                    widget = QTextEdit()
                else:
                    widget = QTextEdit()
                    widget.setReadOnly(True)
                    widget.setFrameShape(QFrame.NoFrame)
                if chunk.style.name:
                    style = named_styles[chunk.style.name]
                else:
                    style = chunk.style

                # Is It A Newline?
                setattr(widget, "newline", chunk.new_line)
                # Set The Range Of Characters
                setattr(widget, "chunk", chunk)

                # Set The Font And Text Formatting
                # TODO: Wrap Text By Doubling Line Height When Line Is To Long
                widget.setFontPointSize(style.fontSize)
                font = QFont(style.font or widget.document().defaultFont())
                font.setPointSize(style.fontSize)
                font.setBold(style.bold)
                font.setUnderline(style.underline)
                font.setStrikeOut(style.strikethrough)
                font.setItalic(style.italic)
                widget.setFont(font)

                # Set The Size Of The Text Box
                # TODO: Is A Tab Always 48 Pixels (0.5 Inch)
                font_metric = QFontMetrics(widget.font()).size(0, chunk.raw_text, 48)
                w = font_metric.width() + 10
                h = font_metric.height() + 0
                widget.setMinimumSize(w, h)
                widget.setMaximumSize(w, h)
                widget.resize(w, h)

                # Remove Scrolling In Text Box
                # TODO: Mouse Wheel Still Scrolls
                widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                widget.setVerticalScrollBar(None)
                # Set Color Of Text
                color = chunk.style.foreground or (0, 0, 0)
                widget.setTextColor(QColor(color[0], color[1], color[2]))

                widget.setText(chunk.raw_text)
                layout.addWidget(widget)
                # https://doc.qt.io/qt-6/qtextedit.html#lineWrapColumnOrWidth-prop
                # else:
                #     label = QLabel()
                #     label.setText(f"<p style='color:rgb{chunk.style.foreground or (0, 0, 0)}'>{chunk.raw_text}</p>")
                #     layout.addWidget(label)
            except IndexError:
                pass

        submit_button = QPushButton("SUBMIT")
        setattr(submit_button, "newline", True)

        @QtCore.Slot()
        def submit_changes():
            changed_chunks = []
            for wid in layout._item_list:
                if isinstance(wid.widget(), QTextEdit):
                    if not wid.widget().isReadOnly():
                        changed_chunks.append(wid.widget())
            doc.submit(changed_chunks)
            print("Submitting")

        submit_button.clicked.connect(submit_changes)
        layout.addWidget(submit_button)

        # Set the layout on the application's window
        self.setLayout(layout)


def main():
    """
    Main Function Of The Editing.
    Handles All Interaction With The Document.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Start Of Document Accessing
    try:
        service = build('docs', 'v1', credentials=creds)

        # Retrieve the documents contents from the Docs service.
        doc = Document(PRODUCT_DOC_ID, service)
        app = QApplication(sys.argv)
        window = Window(doc.get_chunks(), doc.named_styles, doc.get_margins(), doc)
        w = int(doc.documentStyle["pageSize"]["width"]["magnitude"] * (96 / 72))
        h = int(doc.documentStyle["pageSize"]["height"]["magnitude"] * (96 / 72))
        window.setMinimumSize(w, h)
        window.setMaximumSize(w, h)
        window.show()
        sys.exit(app.exec())
        # 'Content #' Are Per New Line

        # Docs: https://developers.google.com/docs/api/reference/rest/v1/documents/request#request
        # requests = [
        #     {
        #         'insertText': {
        #             'location': {
        #                 'index': 25,
        #             },
        #             'text': "Hello"
        #         }
        #     },
        #     {
        #         'insertText': {
        #             'location': {
        #                 'index': 50,
        #             },
        #             'text': "World"
        #         }
        #     },
        # ]
        #
        # # Sends The Request
        # service.documents().batchUpdate(documentId=DOCUMENT_ID, body={'requests': requests}).execute()
    except HttpError as err:
        print(err)


if __name__ == '__main__':
    main()
