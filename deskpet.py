import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QFileDialog, 
                           QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                           QMessageBox, QDialog, QSlider, QCheckBox, QMenu, 
                           QGraphicsBlurEffect, QGraphicsScene, QGraphicsView)
from PyQt5.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal, QRectF
from PyQt5.QtGui import QPixmap, QTransform, QPainter, QColor, QLinearGradient
import ctypes
import json
from itertools import cycle

# Hide console window
if sys.platform == 'win32':
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class ReminderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        self.setWindowTitle("Reminder")
        
        # Style for the reminder window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
                border: 2px solid #c0c0c0;
                border-radius: 10px;
            }
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding: 10px;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2473a7;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        label = QLabel("Hydration check")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.hide)
        ok_button.setCursor(Qt.PointingHandCursor)  # Change cursor on hover
        layout.addWidget(ok_button)
        
        self.setFixedSize(200, 120)

class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.PointingHandCursor)  # Add hand cursor on hover
        
    def hitButton(self, pos):
        return self.contentsRect().contains(pos)  # Make entire widget clickable
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the background
        if self.isChecked():
            painter.setBrush(QColor("#34C759"))  # iOS green
        else:
            painter.setBrush(QColor("#E9E9EA"))  # Light gray
            
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        # Draw the handle (white circle)
        painter.setBrush(QColor("white"))
        if self.isChecked():
            painter.drawEllipse(22, 2, 20, 20)  # Right position
        else:
            painter.drawEllipse(2, 2, 20, 20)   # Left position

class SpriteAnimation:
    def __init__(self, sprite_sheet, animation_data):
        self.sprite_sheet = QPixmap(sprite_sheet)
        
        with open(animation_data, 'r') as f:
            self.data = json.load(f)
            
        self.frames = {}
        self.frame_cycles = {}
        
        # Group frames by animation type
        walk_right = []
        walk_left = []
        idle_right = []
        idle_left = []
        
        for frame_name, frame_data in self.data['frames'].items():
            frame_rect = frame_data['frame']
            duration = frame_data['duration']
            
            # Slow down idle animations by multiplying duration
            if 'idle-' in frame_name.lower():
                duration *= 3  # Makes idle animations 3x slower
                
            x, y = frame_rect['x'], frame_rect['y']
            w, h = frame_rect['w'], frame_rect['h']
            
            frame_pixmap = self.sprite_sheet.copy(x, y, w, h)
            
            if 'walk-right' in frame_name.lower():
                walk_right.append((frame_pixmap, duration))
            elif 'walk-left' in frame_name.lower():
                walk_left.append((frame_pixmap, duration))
            elif 'idle-right' in frame_name.lower():
                idle_right.append((frame_pixmap, duration))
            elif 'idle-left' in frame_name.lower():
                idle_left.append((frame_pixmap, duration))
        
        self.frames = {
            'walking-right': walk_right,
            'walking-left': walk_left,
            'idle-right': idle_right,
            'idle-left': idle_left
        }
        
        # Create cycles for each animation
        self.frame_cycles = {
            name: cycle(frames) 
            for name, frames in self.frames.items()
        }

class SpriteSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.selected_sprite = None
        self.pet = None  # Store reference to the pet
        # Calculate fixed sprite size (what size 75 would have been)
        self.sprite_size = int(65 + (75 - 1) * (65/99))  # ~98 pixels
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Updated style for frosted glass effect
        self.setStyleSheet("""
            QDialog {
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                background-color: rgba(255, 255, 255, 0.92);
            }
            
            #titleBar {
                background-color: transparent;
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
            }
            
            /* Custom title bar styling */
            #closeButton, #minimizeButton {
                background-color: transparent;
                border: none;
                border-radius: 10px;
                min-width: 20px;
                min-height: 20px;
                padding: 4px;
                color: #2c3e50;
                font-size: 16px;
            }
            
            #closeButton:hover {
                background-color: rgba(255, 0, 0, 0.7);
                color: white;
            }
            
            #minimizeButton:hover {
                background-color: rgba(128, 128, 128, 0.3);
                color: white;
            }
            
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 12px;
                min-width: 80px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2473a7;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QSlider {
                margin: 10px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #e0e0e0;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: none;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #2980b9;
            }
            QCheckBox {
                color: #2c3e50;
                font-size: 12px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #bdc3c7;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 2px solid #3498db;
            }
            
            #startButton {
                background-color: #FA8E24;  /* Resting state color */
                border: none;
                color: black;  /* Changed to black text */
                padding: 12px 24px;  /* Added horizontal padding */
                border-radius: 16px;  /* Half of height (32px) for pill shape */
                font-size: 14px;
                min-width: 200px;
                height: 32px;  /* Fixed height */
                max-height: 32px;  /* Added to force height */
            }
            
            #startButton:hover {
                background-color: #DD7714;
            }
            
            #startButton:disabled {
                background-color: #EDEDED;
                color: #808080;
            }
        """)
        
        # Add animation properties
        self.animation = SpriteAnimation('goose.png', 'goose.json')
        self.current_frame = None
        self.frame_time = 0
        
        # Add animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_preview_animation)
        self.animation_timer.start(16)  # ~60 FPS
        
        self.initUI()
        
    def initUI(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Remove spacing between layouts
        
        # Add custom title bar
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(20, 20, 20, 20)  # Increased padding around logo
        
        # Add logo
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("logo.png")
            if not logo_pixmap.isNull():
                scaled_logo = logo_pixmap.scaled(96, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Reduced from 120x40 to 96x32
                logo_label.setPixmap(scaled_logo)
                logo_label.setFixedSize(96, 32)  # Reduced from 120x40 to 96x32
        except:
            print("Logo file not found or invalid")
        
        # Add window controls with reduced spacing
        minimize_btn = QPushButton("−")
        minimize_btn.setObjectName("minimizeButton")
        minimize_btn.clicked.connect(self.showMinimized)
        
        close_btn = QPushButton("×")
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self.close)
        
        title_bar_layout.addWidget(logo_label)
        title_bar_layout.addStretch()
        title_bar_layout.setSpacing(4)  # Added reduced spacing between buttons
        title_bar_layout.addWidget(minimize_btn)
        title_bar_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        # Content layout with consistent margins
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 20)
        
        # Container for centered preview
        preview_container = QHBoxLayout()
        preview_container.addStretch()
        
        # Preview section
        self.preview = QLabel()
        self.preview.setFixedSize(96, 96)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)
        preview_container.addWidget(self.preview)
        preview_container.addStretch()
        content_layout.addLayout(preview_container)
        
        # Add some space after the preview
        content_layout.addSpacing(20)  # Match the top padding
        
        # Image selection
        select_container = QHBoxLayout()
        select_container.addStretch()
        select_btn = QPushButton('Select Sprite Image')
        select_btn.clicked.connect(self.select_sprite)
        select_container.addWidget(select_btn)
        select_container.addStretch()
        content_layout.addLayout(select_container)
        
        # Add some space
        content_layout.addSpacing(10)
        
        # Hydration timer
        hydration_layout = QHBoxLayout()
        hydration_label = QLabel("Hydration reminder")
        hydration_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        self.hydration_checkbox = ToggleSwitch()
        hydration_layout.addWidget(hydration_label)
        hydration_layout.addSpacing(10)  # Reduced from 20px to 10px to match slider spacing
        hydration_layout.addWidget(self.hydration_checkbox)
        hydration_layout.addStretch()
        content_layout.addLayout(hydration_layout)
        
        # Hydration timer
        timer_layout = QHBoxLayout()
        timer_label = QLabel("Reminder Interval:")
        self.timer_slider = QSlider(Qt.Horizontal)
        self.timer_slider.setMinimum(5)
        self.timer_slider.setMaximum(3600)
        self.timer_slider.setValue(1200)  # Changed from 300 (5 minutes) to 1200 (20 minutes)
        self.timer_display = QLabel("20 minutes")  # Updated initial display text
        self.timer_display.setMinimumWidth(80)
        
        self.timer_slider.valueChanged.connect(self.update_timer_display)
        
        timer_layout.addWidget(timer_label)
        timer_layout.addWidget(self.timer_slider)
        timer_layout.addWidget(self.timer_display)
        content_layout.addLayout(timer_layout)
        
        # Add some space before the start button
        content_layout.addSpacing(10)
        
        # Start button in container
        start_container = QHBoxLayout()
        start_container.setContentsMargins(0, 0, 0, 0)  # Remove container margins
        self.start_btn = QPushButton('Start deskpet')
        self.start_btn.setObjectName("startButton")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.toggle_pet)
        self.start_btn.setFixedSize(360, 32)  # Increased width to match bottom padding
        start_container.addWidget(self.start_btn)
        content_layout.addLayout(start_container)
        
        main_layout.addLayout(content_layout)
        
        # Add methods for window dragging
        self.oldPos = None
    
    def update_timer_display(self, value):
        if value < 60:
            self.timer_display.setText(f"{value} seconds")
        else:
            minutes = value // 60
            seconds = value % 60
            if seconds == 0:
                self.timer_display.setText(f"{minutes} minutes")
            else:
                self.timer_display.setText(f"{minutes} min {seconds} sec")
    
    def select_sprite(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Sprite Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_name:
            pixmap = QPixmap(file_name)
            if not pixmap.isNull():
                self.selected_sprite = pixmap
                self.update_preview_size(self.sprite_size)
                self.start_btn.setEnabled(True)
            else:
                QMessageBox.warning(self, "Error", "Invalid image file!")
    
    def update_preview_size(self, size):
        if self.selected_sprite:
            scaled_preview = self.selected_sprite.scaled(
                size, size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview.setPixmap(scaled_preview)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
    
    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = event.globalPos() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()
    
    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create a stronger blur effect
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(20)  # Increased from 10 to 20
        
        # Make the background more transparent to enhance blur visibility
        painter.setBrush(QColor(255, 255, 255, 140))  # Reduced opacity from 178 to 140
        painter.setPen(Qt.NoPen)
        
        # Draw the main background
        painter.drawRoundedRect(self.rect(), 20, 20)
        
        # Enhanced gradient effect
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 140))  # Matching opacity
        gradient.setColorAt(0.5, QColor(255, 255, 255, 120))  # Added middle point
        gradient.setColorAt(1, QColor(255, 255, 255, 100))  # More transparent at bottom
        painter.setBrush(gradient)
        painter.drawRoundedRect(self.rect(), 20, 20)

    def enableBlur(self):
        if sys.platform == 'win32':
            try:
                from win32gui import DwmEnableBlurBehindWindow
                from win32api import GetModuleHandle
                from win32con import WS_EX_LAYERED
                from win32gui import SetWindowLong, GetWindowLong, GWL_EXSTYLE
                
                hwnd = self.winId().__int__()
                
                # Enable blur behind window with stronger effect
                class ACCENTPOLICY(ctypes.Structure):
                    _fields_ = [
                        ('AccentState', ctypes.c_uint),
                        ('AccentFlags', ctypes.c_uint),
                        ('GradientColor', ctypes.c_uint),
                        ('AnimationId', ctypes.c_uint)
                    ]

                class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
                    _fields_ = [
                        ('Attribute', ctypes.c_int),
                        ('Data', ctypes.POINTER(ctypes.c_int)),
                        ('SizeOfData', ctypes.c_size_t)
                    ]

                accent = ACCENTPOLICY()
                accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
                accent.AccentFlags = 0  # Set to 0 for maximum blur
                accent.GradientColor = 0
                
                data = WINDOWCOMPOSITIONATTRIBDATA()
                data.Attribute = 19  # WCA_ACCENT_POLICY
                data.SizeOfData = ctypes.sizeof(accent)
                data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(ctypes.c_int))
                
                SetWindowCompositionAttribute = ctypes.windll.user32.SetWindowCompositionAttribute
                SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
                
            except ImportError:
                pass

    def showEvent(self, event):
        super().showEvent(event)
        self.enableBlur()

    def update_preview_animation(self):
        if self.current_frame is None or self.frame_time <= 0:
            self.current_frame, duration = next(self.animation.frame_cycles['idle-right'])
            self.frame_time = duration
            scaled_frame = self.current_frame.scaled(
                96, 96,  # Preview box size (reduced from 128)
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview.setPixmap(scaled_frame)
        self.frame_time -= 16

    def toggle_pet(self):
        if self.pet is None:
            # Create and show the pet
            self.pet = DesktopPet(
                self.sprite_size,
                150,  # travel range
                self.hydration_checkbox.isChecked(),
                self.timer_slider.value()
            )
            self.start_btn.setText("Stop deskpet")
        else:
            # Close the pet
            self.pet.close()
            self.pet = None
            self.start_btn.setText("Start deskpet")

class DesktopPet(QMainWindow):
    def __init__(self, sprite_size, max_travel, hydration_enabled=False, hydration_interval=300):
        super().__init__()
        self.sprite_size = sprite_size
        self.max_travel = max_travel
        self.hydration_enabled = hydration_enabled
        self.hydration_interval = hydration_interval
        self.start_x = None
        self.reminder_window = ReminderWindow()
        
        # Load animations
        self.animation = SpriteAnimation('goose.png', 'goose.json')
        self.current_animation = 'idle-right'
        self.current_frame = None
        self.frame_time = 0
        
        # Add animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(16)  # ~60 FPS
        
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.pet = QLabel(self)
        self.pet.setGeometry(0, 0, self.sprite_size, self.sprite_size)
        
        self.x = 500
        self.y = 500
        self.direction = 1
        self.is_moving = False
        self.is_dragging = False
        self.drag_offset = None
        
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_position)
        self.move_timer.start(50)
        
        self.decision_timer = QTimer(self)
        self.decision_timer.timeout.connect(self.make_decision)
        self.decision_timer.start(3000)
        
        if self.hydration_enabled:
            self.hydration_timer = QTimer(self)
            self.hydration_timer.timeout.connect(self.hydration_check)
            self.hydration_timer.start(self.hydration_interval * 1000)
        
        self.setGeometry(self.x, self.y, self.sprite_size, self.sprite_size)
        self.show()
        
        if self.start_x is None:
            self.start_x = self.x
    
    def hydration_check(self):
        self.reminder_window.show()
        self.reminder_window.raise_()
        self.reminder_window.activateWindow()
    
    def update_animation(self):
        if self.current_frame is None or self.frame_time <= 0:
            self.current_frame, duration = next(self.animation.frame_cycles[self.current_animation])
            self.frame_time = duration
            scaled_frame = self.current_frame.scaled(
                self.sprite_size, self.sprite_size,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.pet.setPixmap(scaled_frame)
        self.frame_time -= 16
    
    def update_position(self):
        if self.is_moving and not self.is_dragging:
            self.x += 2 * self.direction
            
            # Update animation based on direction
            self.current_animation = 'walking-right' if self.direction > 0 else 'walking-left'
            
            if abs(self.x - self.start_x) > self.max_travel // 2:
                if self.x > self.start_x:
                    self.x = self.start_x + self.max_travel // 2
                    self.direction = -1
                else:
                    self.x = self.start_x - self.max_travel // 2
                    self.direction = 1
            
            self.move(self.x, self.y)
    
    def make_decision(self):
        import random
        self.is_moving = random.choice([True, False])
        if not self.is_moving:
            # Set idle animation based on last direction
            self.current_animation = 'idle-right' if self.direction > 0 else 'idle-left'
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_offset = event.pos()
            self.move_timer.stop()
            self.decision_timer.stop()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            new_pos = event.globalPos() - self.drag_offset
            self.x = new_pos.x()
            self.y = new_pos.y()
            self.start_x = self.x
            self.move(self.x, self.y)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.move_timer.start()
            self.decision_timer.start()
    
    def mouseDoubleClickEvent(self, event):
        self.current_animation = 'idle-right'
        self.pet.setPixmap(self.animation.frames[self.current_animation][0])
    
    def show_context_menu(self, position):
        menu = QMenu()
        exit_action = menu.addAction("Exit")
        action = menu.exec_(position)
        
        if action == exit_action:
            QApplication.quit()

def main():
    app = QApplication(sys.argv)
    
    # Show settings dialog
    selector = SpriteSelector()
    selector.selected_sprite = QPixmap("goose.png")
    selector.start_btn.setEnabled(True)
    
    # Find the select button in the content layout and hide it
    for child in selector.findChildren(QPushButton):
        if child.text() == 'Select Sprite Image':
            child.setVisible(False)
            break
            
    selector.preview.setPixmap(selector.selected_sprite.scaled(
        selector.sprite_size, 
        selector.sprite_size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    ))
    
    # Show the selector window instead of using exec_()
    selector.show()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
