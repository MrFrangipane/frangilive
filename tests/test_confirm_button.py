import os
import unittest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from frangilive.ui.widgets import ConfirmButton

os.environ["QT_QPA_PLATFORM"] = "offscreen"


class TestConfirmButton(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app_qt = QApplication.instance() or QApplication([])

    def test_single_click_on_hold_completion(self):
        """Holding until duration ends must emit clicked exactly once, and releasing must not emit a second click."""
        btn = ConfirmButton(text="Delete", confirm_text="Sure ?", duration=50)
        clicks = []
        btn.clicked.connect(lambda: clicks.append(1))

        # Press and hold
        QTest.mousePress(btn, Qt.MouseButton.LeftButton)
        # Wait past duration for timer completion
        QTest.qWait(100)
        self.assertEqual(len(clicks), 1)

        # Release after completion
        QTest.mouseRelease(btn, Qt.MouseButton.LeftButton)
        QTest.qWait(20)
        # Must still be exactly 1, not 2
        self.assertEqual(len(clicks), 1)

    def test_release_before_duration_cancels(self):
        """Releasing before duration must cancel the action without emitting clicked."""
        btn = ConfirmButton(text="Delete", confirm_text="Sure ?", duration=100)
        clicks = []
        btn.clicked.connect(lambda: clicks.append(1))

        # Press
        QTest.mousePress(btn, Qt.MouseButton.LeftButton)
        # Wait less than duration
        QTest.qWait(20)
        # Release early
        QTest.mouseRelease(btn, Qt.MouseButton.LeftButton)
        QTest.qWait(150)

        self.assertEqual(len(clicks), 0)
        self.assertEqual(btn.text(), "Delete")

    def test_programmatic_click(self):
        """Calling click() programmatically emits clicked signal."""
        btn = ConfirmButton(text="Delete", confirm_text="Sure ?", duration=50)
        clicks = []
        btn.clicked.connect(lambda: clicks.append(1))

        btn.click()
        self.assertEqual(len(clicks), 1)


if __name__ == "__main__":
    unittest.main()
