from PySide6.QtWidgets import QPushButton, QSizePolicy


def make_button(text: str, checkable=True, color=None):
    button = QPushButton(text)

    stylesheet = "QPushButton:enabled {font-size: 12pt; font-weight: bold;"
    if color is not None:
        stylesheet += f"background-color: {color};"
    stylesheet += "}"
    button.setStyleSheet(stylesheet)

    button.setMinimumWidth(120)
    button.setCheckable(checkable)
    button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return button
