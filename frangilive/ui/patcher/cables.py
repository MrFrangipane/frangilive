from PySide6.QtGui import QPainter, Qt
from PySide6.QtWidgets import QWidget


class CablesWidget(QWidget):
    def __init__(self, left_device_count: int, right_device_count: int, parent=None):
        super().__init__(parent)
        self._connections: list[tuple[int, int]] = []
        self._left_device_count = left_device_count
        self._right_device_count = right_device_count

    def set_left_device_count(self, device_count: int):
        self._left_device_count = device_count

    def set_right_device_count(self, device_count: int):
        self._right_device_count = device_count

    def clear_connections(self):
        self._connections.clear()

    def add_connection(self, left: int, right: int):
        if (left, right) in self._connections:
            return
        self._connections.append((left, right))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = event.rect().adjusted(1, 1, -1, -1)

        left_height = rect.height() / self._left_device_count
        left_half_height = left_height / 2

        right_height = rect.height() / self._right_device_count
        right_half_height = right_height / 2

        pen = painter.pen()
        pen.setWidth(2)

        for left in range(self._left_device_count):
            for right in range(self._right_device_count):
                if (left, right) not in self._connections:
                    continue

                painter.setPen(pen)
                painter.drawLine(
                    0, int(left_height * left + left_half_height),
                    rect.width(), int(right_height * right + right_half_height),
                )

        painter.end()
