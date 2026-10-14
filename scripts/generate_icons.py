
import sys
import os
import json
from PySide6.QtGui import QPainter, QColor, QImage, QBrush, QPen, QFont
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QApplication


def generate_common_elektron(painter, color_accent, label, sub_label):
    # Chassis - Elektron devices are dark metallic grey/black
    painter.setBrush(QBrush(QColor(25, 25, 25)))
    painter.setPen(QPen(QColor(0, 0, 0), 1))
    # Main body
    body_rect = QRectF(8, 15, 112, 98)
    painter.drawRoundedRect(body_rect, 6, 6)
    
    # Faceplate detail (slightly lighter)
    painter.setBrush(QBrush(QColor(35, 35, 35)))
    face_rect = QRectF(12, 19, 104, 90)
    painter.drawRoundedRect(face_rect, 4, 4)
    
    # Screen - OLED black
    painter.setBrush(QBrush(QColor(10, 10, 10)))
    painter.setPen(QPen(QColor(60, 60, 60), 1))
    screen_rect = QRectF(22, 30, 42, 28)
    painter.drawRect(screen_rect)
    
    # Encoders - 8 knobs (2 rows of 4)
    painter.setBrush(QBrush(QColor(20, 20, 20)))
    painter.setPen(QPen(QColor(0, 0, 0), 1))
    knob_radius = 4
    for row in range(2):
        for col in range(4):
            cx = 74 + col * 10
            cy = 34 + row * 16
            painter.drawEllipse(QPointF(cx, cy), knob_radius, knob_radius)
            # Knob cap detail
            painter.setPen(QPen(QColor(60, 60, 60), 0.5))
            painter.drawEllipse(QPointF(cx, cy), knob_radius - 1, knob_radius - 1)
            painter.setPen(QPen(QColor(0, 0, 0), 1))

    # Buttons - 16 trigs at bottom.
    painter.setBrush(QBrush(QColor(50, 50, 50)))
    trig_y = 88
    trig_width = 5
    trig_height = 7
    trig_spacing = 6.2
    for i in range(16):
        tx = 16 + i * trig_spacing
        painter.drawRect(QRectF(tx, trig_y, trig_width, trig_height))
        # Add some "LED" color to a few buttons
        if i in [0, 4, 8, 12]:
            painter.fillRect(QRectF(tx + 1, trig_y + 1, trig_width - 2, 1), color_accent)

    # Label
    painter.setPen(QPen(QColor(180, 180, 180)))
    font = QFont("Arial", 7, QFont.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(22, 60, 50, 10), Qt.AlignLeft | Qt.AlignVCenter, label)
    
    # Logo sub-label
    painter.setPen(QPen(color_accent))
    painter.drawText(QRectF(90, 60, 20, 10), Qt.AlignRight | Qt.AlignVCenter, sub_label)

def generate_icon(path, generator_func, *args, scale=2.0):
    base_size = 128
    size = int(base_size * scale)
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.scale(scale, scale)
    generator_func(painter, *args)
    painter.end()
    image.save(path, "PNG")

def generate_syntakt_icon(path, scale=2.0):
    generate_icon(path, generate_common_elektron, QColor(255, 0, 100), "SYNTAKT", "ST", scale=scale)

def generate_digitakt_icon(path, scale=2.0):
    generate_icon(path, generate_common_elektron, QColor(255, 200, 0), "DIGITAKT", "DT", scale=scale)

def generate_digitone_icon(path, scale=2.0):
    generate_icon(path, generate_common_elektron, QColor(0, 255, 150), "DIGITONE", "DN", scale=scale)

def draw_microphone(painter):
    # Handle
    painter.setBrush(QBrush(QColor(40, 40, 40)))
    painter.setPen(QPen(QColor(20, 20, 20), 2))
    painter.drawRoundedRect(56, 60, 16, 50, 4, 4)
    
    # Head
    painter.setBrush(QBrush(QColor(80, 80, 80)))
    painter.drawEllipse(44, 20, 40, 45)
    
    # Grid pattern on head
    painter.setPen(QPen(QColor(120, 120, 120), 1))
    for i in range(5):
        painter.drawLine(44, 28 + i*8, 84, 28 + i*8)
    for i in range(5):
        painter.drawLine(48 + i*8, 20, 48 + i*8, 65)

def generate_microphone_icon(path, scale=2.0):
    generate_icon(path, draw_microphone, scale=scale)

def draw_main_lr(painter):
    # Speaker box
    painter.setBrush(QBrush(QColor(30, 30, 30)))
    painter.setPen(QPen(QColor(10, 10, 10), 2))
    painter.drawRoundedRect(34, 24, 60, 80, 5, 5)
    
    # Woofers
    painter.setBrush(QBrush(QColor(50, 50, 50)))
    painter.drawEllipse(44, 60, 40, 40)
    painter.drawEllipse(54, 34, 20, 20)
    
    # Cones
    painter.setBrush(QBrush(QColor(70, 70, 70)))
    painter.drawEllipse(59, 75, 10, 10)
    painter.drawEllipse(61, 41, 6, 6)

def generate_main_lr_icon(path, scale=2.0):
    generate_icon(path, draw_main_lr, scale=scale)

def generate_moogerfooger_base(painter, label):
    # Chassis
    painter.setBrush(QBrush(QColor(20, 20, 20)))
    painter.setPen(QPen(QColor(0, 0, 0), 1))
    painter.drawRect(20, 20, 88, 88)
    
    # Wood sides
    painter.setBrush(QBrush(QColor(100, 50, 20)))
    painter.drawRect(12, 20, 8, 88)
    painter.drawRect(108, 20, 8, 88)
    
    # Faceplate label
    painter.setPen(QPen(QColor(200, 200, 200)))
    font = QFont("Arial", 6, QFont.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(20, 25, 88, 10), Qt.AlignCenter, label)

def draw_mf101(painter):
    generate_moogerfooger_base(painter, "LOWPASS FILTER")
    # Big knobs
    painter.setBrush(QBrush(QColor(40, 40, 40)))
    painter.drawEllipse(35, 40, 22, 22)
    painter.drawEllipse(71, 40, 22, 22)
    # Small knobs
    painter.drawEllipse(30, 75, 12, 12)
    painter.drawEllipse(58, 75, 12, 12)
    painter.drawEllipse(86, 75, 12, 12)

def generate_mf101_icon(path, scale=2.0):
    generate_icon(path, draw_mf101, scale=scale)

def draw_murf(painter):
    generate_moogerfooger_base(painter, "MuRF")
    # Sliders
    for i in range(8):
        sx = 30 + i * 9
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawLine(sx, 45, sx, 85)
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.setPen(Qt.NoPen)
        slider_y = 50 + (i % 3) * 10
        painter.drawRect(sx - 3, slider_y, 6, 4)

def generate_murf_icon(path, scale=2.0):
    generate_icon(path, draw_murf, scale=scale)

def draw_time_factor(painter):
    # Chassis - Dark charcoal metallic
    painter.setBrush(QBrush(QColor(35, 38, 41)))
    painter.setPen(QPen(QColor(10, 10, 10), 1))
    # Main body
    painter.drawRoundedRect(10, 10, 108, 108, 6, 6)
    
    # Top Section: Knobs
    # Row 1: 6 knobs
    painter.setBrush(QBrush(QColor(20, 20, 20)))
    painter.setPen(QPen(QColor(80, 80, 80), 0.5))
    knob_r = 4.5
    for i in range(6):
        cx = 19 + i * 18
        cy = 25
        painter.drawEllipse(QPointF(cx, cy), knob_r, knob_r)
        # Indicator line
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        painter.drawLine(QPointF(cx, cy), QPointF(cx, cy - 3))
        painter.setPen(QPen(QColor(80, 80, 80), 0.5))

    # Row 2: 1 button/encoder + 4 knobs
    # Button on the left
    painter.setBrush(QBrush(QColor(60, 60, 60)))
    painter.drawEllipse(QPointF(19, 48), 4, 4)
    # 4 Knobs
    painter.setBrush(QBrush(QColor(20, 20, 20)))
    for i in range(4):
        cx = 40 + i * 21
        cy = 48
        painter.drawEllipse(QPointF(cx, cy), knob_r, knob_r)
        # Indicator line
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        painter.drawLine(QPointF(cx, cy), QPointF(cx, cy - 3))
        painter.setPen(QPen(QColor(80, 80, 80), 0.5))

    # Middle Section: Blue Stripe
    painter.setBrush(QBrush(QColor(45, 102, 196))) # Eventide Blue
    painter.setPen(Qt.NoPen)
    painter.drawRect(10, 62, 108, 24)

    # Dot matrix display (Yellow on Black)
    painter.setBrush(QBrush(QColor(20, 20, 20)))
    painter.drawRect(35, 66, 45, 16)
    
    # Draw some yellow dots to simulate dot matrix
    painter.setBrush(QBrush(QColor(255, 230, 0)))
    for r in range(3):
        for c in range(10):
            painter.drawEllipse(QPointF(38 + c*4, 69 + r*5), 0.8, 0.8)

    # Branding in Blue Stripe
    painter.setPen(QPen(QColor(255, 255, 255)))
    font = QFont("Arial", 6, QFont.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(82, 63, 34, 12), Qt.AlignLeft | Qt.AlignVCenter, "Eventide")
    font.setPointSize(4)
    painter.setFont(font)
    painter.drawText(QRectF(82, 73, 34, 10), Qt.AlignLeft | Qt.AlignVCenter, "TIMEFACTOR")

    # Bottom Section: Footswitches
    painter.setBrush(QBrush(QColor(180, 180, 180)))
    painter.setPen(QPen(QColor(50, 50, 50), 1))
    for i in range(3):
        fs_x = 28 + i * 36
        fs_y = 102
        painter.drawEllipse(QPointF(fs_x, fs_y), 7, 7)
        painter.setBrush(QBrush(QColor(210, 210, 210)))
        painter.drawEllipse(QPointF(fs_x, fs_y), 3.5, 3.5)
        painter.setBrush(QBrush(QColor(180, 180, 180)))
        
        # Labels for footswitches
        painter.setPen(QPen(QColor(150, 150, 150)))
        font.setPointSize(4)
        painter.setFont(font)
        labels = ["Active", "Repeat", "Tap"]
        painter.drawText(QRectF(fs_x - 15, fs_y + 8, 30, 8), Qt.AlignCenter, labels[i])

def generate_time_factor_icon(path, scale=2.0):
    generate_icon(path, draw_time_factor, scale=scale)

def draw_big_sky(painter):
    # Chassis - Strymon blue
    painter.setBrush(QBrush(QColor(0, 150, 200)))
    painter.setPen(QPen(QColor(0, 100, 150), 1))
    painter.drawRoundedRect(15, 20, 98, 88, 5, 5)
    
    # Display
    painter.setBrush(QBrush(QColor(20, 20, 20)))
    painter.drawRect(25, 30, 40, 20)
    painter.setPen(QPen(QColor(0, 255, 100)))
    painter.drawText(QRectF(25, 30, 40, 20), Qt.AlignCenter, "Cloud")
    
    # Knobs
    painter.setBrush(QBrush(QColor(220, 220, 220)))
    painter.drawEllipse(75, 30, 15, 15)
    for i in range(3):
        painter.drawEllipse(25 + i*28, 60, 12, 12)
    for i in range(2):
        painter.drawEllipse(40 + i*28, 85, 12, 12)

def generate_big_sky_icon(path, scale=2.0):
    generate_icon(path, draw_big_sky, scale=scale)

if __name__ == "__main__":
    # Configuration
    ICON_SCALE = 2.0  # Make icons twice larger by default
    
    # Create an app instance to avoid potential issues with QPainter
    app = QApplication(sys.argv)
    
    icons_dir = os.path.join("frangilive", "resources", "icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    devices_path = os.path.join("frangilive", "resources", "devices.json")
    with open(devices_path, "r") as f:
        devices_data = json.load(f)
    
    generators = {
        "Syntakt": generate_syntakt_icon,
        "Digitakt": generate_digitakt_icon,
        "Digitone": generate_digitone_icon,
        "Microphone": generate_microphone_icon,
        "Main LR": generate_main_lr_icon,
        "MF-101": generate_mf101_icon,
        "MuRF": generate_murf_icon,
        "Time Factor": generate_time_factor_icon,
        "Big Sky": generate_big_sky_icon,
    }
    
    for instrument in devices_data.get("audio_instruments", []):
        name = instrument.get("name")
        if name in generators:
            filename = name.lower().replace(" ", "_") + ".png"
            path = os.path.join(icons_dir, filename)
            generators[name](path, scale=ICON_SCALE)
            print(f"Generated icon for {name} (scale={ICON_SCALE}) at {path}")
        else:
            print(f"No generator found for {name}")
