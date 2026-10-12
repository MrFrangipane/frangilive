from PySide6.QtWidgets import QPushButton, QSizePolicy

from pyside6helpers.confirm_button import ConfirmButton


def make_button(text: str, checkable=True, confirm=False, color=None):
    if confirm:
        button = ConfirmButton(text)
    else:
        button = QPushButton(text)

    if color is not None:
        button.setStyleSheet(f"background-color: {color};")

    button.setMinimumWidth(120)
    button.setCheckable(checkable)
    button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return button
