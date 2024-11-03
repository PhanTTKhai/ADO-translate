import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import pytesseract
from deep_translator import GoogleTranslator
import io
from PIL import Image

# Set the path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class TranslationWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Translation')
        # Optionally, set the window to stay on top (commented out here)
        # self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # Create a text edit widget to display the translated text
        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setReadOnly(True)
        # Set font size
        font = QtGui.QFont()
        font.setPointSize(12)
        self.text_edit.setFont(font)
        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        # Set initial size
        self.resize(400, 300)

    def update_text(self, text):
        self.text_edit.setText(text)

class ScreenshotWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        # Variables to handle moving and resizing the window
        self.offset = None
        self.resizing = False
        self.resizingDirection = None
        self.margin = 50  # Margin for detecting resize

        # Timer for continuous translation
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.capture_screenshot)

        # Translation window
        self.translation_window = TranslationWindow()
        self.translation_window.show()

    def initUI(self):
        self.setWindowTitle('Screenshot Tool')

        # Remove window borders and keep it on top
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        # Make the window semi-transparent
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Set initial size
        self.resize(400, 300)

        # Create a toggle button for continuous capture
        self.capture_button = QtWidgets.QPushButton('Start', self)
        self.capture_button.setCheckable(True)
        self.capture_button.clicked.connect(self.toggle_capture)

        # Make the button semi-transparent
        self.capture_button.setStyleSheet("background-color: rgba(255, 255, 255, 150);")

        # Layout the button at the bottom-right corner
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.capture_button)
        layout.setAlignment(self.capture_button, QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def toggle_capture(self):
        if self.capture_button.isChecked():
            self.capture_button.setText('Stop')
            # Start the timer with an interval (e.g., every 1 second)
            self.timer.start(100)
        else:
            self.capture_button.setText('Start')
            self.timer.stop()

    def capture_screenshot(self):
        # Bring the window to the top
        self.raise_()

        # Get the geometry of the window
        x = self.x()
        y = self.y()
        w = self.width()
        h = self.height()

        # Grab the area of the screen under the window
        screen = QtWidgets.QApplication.primaryScreen()
        screenshot = screen.grabWindow(0, x, y, w, h)

        # Translate the screenshot
        self.translate(screenshot)

    def paintEvent(self, event):
        # Draw a semi-transparent rectangle to represent the window
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtCore.Qt.red, 2)
        painter.setPen(pen)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 20))
        painter.setBrush(brush)
        rect = self.rect()
        painter.drawRect(rect)

    # Implement mouse events to move and resize the window
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            # Check if the cursor is near the edge for resizing
            pos = event.pos()
            x = pos.x()
            y = pos.y()
            w = self.width()
            h = self.height()
            margin = self.margin

            # Set resizing flags
            self.resizingTop = y < margin
            self.resizingBottom = y > h - margin
            self.resizingLeft = x < margin
            self.resizingRight = x > w - margin

            if self.resizingTop or self.resizingBottom or self.resizingLeft or self.resizingRight:
                self.resizing = True
                self.originalRect = self.geometry()
                self.mousePressPos = event.globalPos()
            else:
                self.offset = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        x = pos.x()
        y = pos.y()
        w = self.width()
        h = self.height()
        margin = self.margin

        # Change cursor if near the edge
        if not self.resizing and not self.offset:
            self.resizingTop = y < margin
            self.resizingBottom = y > h - margin
            self.resizingLeft = x < margin
            self.resizingRight = x > w - margin

            hor = self.resizingLeft or self.resizingRight
            ver = self.resizingTop or self.resizingBottom

            if hor and ver:
                if (self.resizingLeft and self.resizingTop) or (self.resizingRight and self.resizingBottom):
                    self.setCursor(QtCore.Qt.SizeFDiagCursor)
                else:
                    self.setCursor(QtCore.Qt.SizeBDiagCursor)
            elif hor:
                self.setCursor(QtCore.Qt.SizeHorCursor)
            elif ver:
                self.setCursor(QtCore.Qt.SizeVerCursor)
            else:
                self.setCursor(QtCore.Qt.ArrowCursor)

        if self.resizing:
            # Handle resizing
            delta = event.globalPos() - self.mousePressPos
            rect = self.originalRect

            newLeft = rect.left()
            newTop = rect.top()
            newRight = rect.right()
            newBottom = rect.bottom()

            if self.resizingLeft:
                newLeft += delta.x()
            if self.resizingRight:
                newRight += delta.x()
            if self.resizingTop:
                newTop += delta.y()
            if self.resizingBottom:
                newBottom += delta.y()

            # Minimum size
            minWidth = 100
            minHeight = 50

            if newRight - newLeft < minWidth:
                if self.resizingLeft:
                    newLeft = newRight - minWidth
                else:
                    newRight = newLeft + minWidth
            if newBottom - newTop < minHeight:
                if self.resizingTop:
                    newTop = newBottom - minHeight
                else:
                    newBottom = newTop + minHeight

            # Apply new geometry
            self.setGeometry(QtCore.QRect(QtCore.QPoint(newLeft, newTop), QtCore.QPoint(newRight, newBottom)))
        elif self.offset is not None:
            # Move the window
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = None
        self.resizing = False
        self.resizingTop = self.resizingBottom = self.resizingLeft = self.resizingRight = False
        self.setCursor(QtCore.Qt.ArrowCursor)

    def translate(self, screenshot):
        # Convert QPixmap to PIL Image
        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QBuffer.ReadWrite)
        screenshot.save(buffer, 'PNG')
        pil_im = Image.open(io.BytesIO(buffer.data()))

        # Extract text from the image
        extracted_text = pytesseract.image_to_string(pil_im, lang='jpn')

        if extracted_text.strip():
            print("Extracted Text:", extracted_text)

            # Translate the extracted text to English
            translated_text = GoogleTranslator(source='auto', target='en').translate(extracted_text)
            # print("Translated Text:", translated_text)
            # Update the translation window
            self.translation_window.update_text(translated_text)
            self.translation_window.raise_()  # Bring the translation window to front
        # else:
        #     print("No text detected.")
        #     self.translation_window.update_text('No text detected.')

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ScreenshotWindow()
    window.show()
    sys.exit(app.exec_())
