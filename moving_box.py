import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from deep_translator import GoogleTranslator
import io
from PIL import Image

class ScreenshotWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        # Variables to handle moving and resizing the window
        self.offset = None
        self.resizing = False
        self.resizingDirection = None
        self.margin = 10  # Reduced margin for detecting resize

        # Timer for continuous translation
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.capture_screenshot)


    def initUI(self):
        self.setWindowTitle('Screenshot Tool')

        # Remove window borders and keep it on top
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        # Make the window semi-transparent
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Enable mouse tracking
        self.setMouseTracking(True)

        # Set initial size
        self.resize(400, 300)

        # Create a toggle button for continuous capture
        self.capture_button = QtWidgets.QPushButton('Start', self)
        self.capture_button.setCheckable(True)
        self.capture_button.clicked.connect(self.toggle_capture)

        # Make the button semi-transparent
        self.capture_button.setStyleSheet("background-color: rgba(255, 255, 255, 150);")

        # Remove the layout and position the button manually
        self.update_button_position()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update button position on window resize
        self.update_button_position()

    def update_button_position(self):
        # Position the button at the bottom-right corner
        button_width = self.capture_button.sizeHint().width()
        button_height = self.capture_button.sizeHint().height()
        self.capture_button.move(self.width() - button_width - 10, self.height() - button_height - 10)

    def toggle_capture(self):
        if self.capture_button.isChecked():
            self.capture_button.setText('Stop')
            # Start the timer with an interval (e.g., every 100 milliseconds)
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
        self.process_screenshot(screenshot)

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
                print("Resizing started")
            else:
                self.offset = event.globalPos() - self.frameGeometry().topLeft()
                print("Moving started")

    def mouseMoveEvent(self, event):
        pos = event.pos()
        x = pos.x()
        y = pos.y()
        w = self.width()
        h = self.height()
        margin = self.margin

        # Debugging: Print cursor position
        # print(f"Mouse Position: ({x}, {y})")

        # Change cursor if near the edge
        if not self.resizing and self.offset is None:
            self.resizingTop = y < margin
            self.resizingBottom = y > h - margin
            self.resizingLeft = x < margin
            self.resizingRight = x > w - margin

            hor = self.resizingLeft or self.resizingRight
            ver = self.resizingTop or self.resizingBottom

            if hor and ver:
                if (self.resizingLeft and self.resizingTop) or (self.resizingRight and self.resizingBottom):
                    self.setCursor(QtCore.Qt.SizeFDiagCursor)
                    # print("Cursor set to SizeFDiagCursor")
                else:
                    self.setCursor(QtCore.Qt.SizeBDiagCursor)
                    # print("Cursor set to SizeBDiagCursor")
            elif hor:
                self.setCursor(QtCore.Qt.SizeHorCursor)
                # print("Cursor set to SizeHorCursor")
            elif ver:
                self.setCursor(QtCore.Qt.SizeVerCursor)
                # print("Cursor set to SizeVerCursor")
            else:
                self.setCursor(QtCore.Qt.ArrowCursor)
                # print("Cursor set to ArrowCursor")

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
            # print(f"Resizing: New geometry set to {self.geometry()}")
        elif self.offset is not None:
            # Move the window
            self.move(event.globalPos() - self.offset)
            # print(f"Moving: Window moved to {self.pos()}")

    def mouseReleaseEvent(self, event):
        self.offset = None
        self.resizing = False
        self.resizingTop = self.resizingBottom = self.resizingLeft = self.resizingRight = False
        self.setCursor(QtCore.Qt.ArrowCursor)
        # print("Mouse released, cursor reset to ArrowCursor")

    def process_screenshot(self, screenshot):
        # Convert QPixmap to PIL Image
        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QBuffer.ReadWrite)
        screenshot.save(buffer, 'PNG')
        pil_im = Image.open(io.BytesIO(buffer.data()))

        # Extract text from the image using OCR
        extracted_text = pytesseract.image_to_string(pil_im)

        # Only print if the text has changed
        if extracted_text.strip() and extracted_text.strip() != self.previous_text:
            self.previous_text = extracted_text.strip()  # Update the previous text
            print("Detected Text:", self.previous_text)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ScreenshotWindow()
    window.show()
    sys.exit(app.exec_())
