from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QPainter, QPalette
from PySide6.QtWidgets import QPushButton


class ConfirmButton(QPushButton):
    """
    A push button that requires holding down for a configurable duration to confirm an action.
    Fires the clicked signal exactly once upon reaching 100% progress and avoids double-firing
    on mouse release.
    """

    def __init__(
        self,
        text: str = "",
        confirm_text: str = "Sure ?",
        duration: int = 1000,
        parent=None,
    ):
        super().__init__(text, parent)
        self._default_text = text
        self._confirm_text = confirm_text
        self._progress = 0.0
        self._triggered = False

        self.animation = QPropertyAnimation(self, b"progress")
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(100.0)
        self.animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.animation.finished.connect(self._on_animation_finished)

    @Property(float)
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, value: float) -> None:
        self._progress = value
        self.update()

    def setText(self, text: str) -> None:
        if (
            self.animation.state() != QPropertyAnimation.State.Running
            and not self._triggered
        ):
            self._default_text = text
        super().setText(text)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._triggered = False
            super().setText(self._confirm_text)
            self.animation.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.animation.state() == QPropertyAnimation.State.Running:
                self.animation.stop()
                self._reset_button()
            self.setDown(False)
            self._triggered = False
            return
        super().mouseReleaseEvent(event)

    def _on_animation_finished(self) -> None:
        if self._progress >= 100.0:
            self._triggered = True
            self.clicked.emit()
        self._reset_button()

    def _reset_button(self) -> None:
        self._progress = 0.0
        super().setText(self._default_text)
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._progress > 0:
            painter = QPainter(self)
            color = self.palette().color(QPalette.ColorRole.Highlight)
            color.setAlpha(100)
            width = int(self.width() * (self._progress / 100.0))
            painter.fillRect(0, 0, width, self.height(), color)
            painter.end()
