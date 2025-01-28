import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QFileDialog, 
                           QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                           QMessageBox, QDialog, QSlider, QCheckBox, QMenu)
from PyQt5.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal, QRectF
from PyQt5.QtGui import QPixmap, QTransform, QPainter, QColor, QLinearGradient, QRegion, QPainterPath, QIcon
import ctypes
import json
from itertools import cycle

# Hide console window
if sys.platform == 'win32':
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class ReminderWindow(QMainWindow):
    def __init__(self, reminder_type="Hydration"):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Reminder")
        
        # Style for the reminder window
        self.setStyleSheet("""
            QMainWindow {
                background-color: transparent;
            }
            QWidget {
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                background-color: rgba(255, 255, 255, 0.92);
            }
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding: 10px;
                border: none;
                background-color: transparent;
            }
            QPushButton {
                background-color: #FA8E24;
                border: none;
                color: black;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #DD7714;
            }
            QPushButton:pressed {
                background-color: #DD7714;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        label = QLabel(f"{reminder_type} check!")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.hide)
        ok_button.setCursor(Qt.PointingHandCursor)
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
            painter.setBrush(QColor("#FA8E24"))  # Changed from #34C759 to #FA8E24
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
        self.pet = None
        self.sprite_size = 96
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Add window icon
        self.setWindowIcon(QIcon('icon.ico'))
        
        # Updated style for frosted glass effect
        self.setStyleSheet("""
            QDialog {
                border-radius: 15px;
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
                background: #FA8E24;  /* Changed from #3498db to #FA8E24 */
                border: none;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #DD7714;  /* Darker version of #FA8E24 for hover state */
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
                background-color: #FA8E24;
                border: none;
                color: black;
                padding: 0px;
                border-radius: 16px;
                font-size: 14px;
                min-width: 360px;
                width: 360px;
                max-width: 360px;
                height: 64px;          /* Doubled from 32px */
                max-height: 64px;      /* Doubled from 32px */
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
        title_bar_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add logo with left alignment matching containers
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("logo.png")
            if not logo_pixmap.isNull():
                scaled_logo = logo_pixmap.scaled(96, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_logo)
                logo_label.setFixedSize(96, 32)
        except:
            print("Logo file not found or invalid")
        
        # Create a container to align logo with settings containers
        logo_container = QHBoxLayout()
        logo_container.setContentsMargins(0, 0, 0, 0)
        logo_container.addWidget(logo_label)
        logo_container.addStretch()
        
        # Add window controls
        title_bar_layout.addLayout(logo_container)
        title_bar_layout.addStretch()
        minimize_btn = QPushButton("−")
        minimize_btn.setObjectName("minimizeButton")
        minimize_btn.clicked.connect(self.showMinimized)
        
        close_btn = QPushButton("×")
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self.close)
        
        title_bar_layout.setSpacing(0)  # Set the spacing to 0 between all items in the layout
        title_bar_layout.addWidget(minimize_btn)
        title_bar_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        # Content layout with consistent margins and centering
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 2, 20, 20)  # Reduced top margin by 8px
        content_layout.setAlignment(Qt.AlignCenter)
        
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
        
        # Container for hydration settings
        hydration_container = QWidget()
        hydration_container.setFixedWidth(360)
        hydration_container.setStyleSheet("""
            QWidget {
                border: 0.5px solid rgba(0, 0, 0, 0.65);
                border-radius: 16px;
                padding: 6px;
            }
            QLabel {
                border: none;
            }
            QSlider {
                border: none;
            }
        """)
        hydration_container_layout = QVBoxLayout(hydration_container)
        hydration_container_layout.setContentsMargins(6, 12, 6, 0)  # Removed bottom padding
        hydration_container_layout.setSpacing(2)  # Minimal spacing between toggle and interval

        # Add all the hydration settings as before
        hydration_layout = QHBoxLayout()
        hydration_layout.setSpacing(4)
        hydration_label = QLabel("Hydration reminder")
        hydration_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                border: none;
            }
        """)
        self.hydration_checkbox = ToggleSwitch()
        hydration_layout.addWidget(hydration_label)
        hydration_layout.addWidget(self.hydration_checkbox)
        hydration_layout.addStretch()
        hydration_container_layout.addLayout(hydration_layout)

        # Hydration timer slider
        timer_layout = QHBoxLayout()
        timer_layout.setSpacing(4)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_label = QLabel("Reminder interval:")
        timer_label.setStyleSheet("border: none;")
        self.timer_slider = QSlider(Qt.Horizontal)
        self.timer_slider.setFixedWidth(150)  # Set fixed width for slider
        self.timer_slider.setMinimum(300)
        self.timer_slider.setMaximum(3600)
        self.timer_slider.setValue(1200)
        self.timer_display = QLabel("20 minutes")
        self.timer_display.setStyleSheet("border: none;")
        self.timer_display.setFixedWidth(80)  # Set fixed width for display label
        self.timer_slider.valueChanged.connect(self.update_timer_display)
        
        timer_layout.addWidget(timer_label)
        timer_layout.addWidget(self.timer_slider)
        timer_layout.addWidget(self.timer_display)
        hydration_container_layout.addLayout(timer_layout)

        content_layout.addWidget(hydration_container, 0, Qt.AlignCenter)
        content_layout.addSpacing(12)  # Reduced spacing between containers

        # Container for posture settings
        posture_container = QWidget()
        posture_container.setFixedWidth(360)
        posture_container.setStyleSheet("""
            QWidget {
                border: 0.5px solid rgba(0, 0, 0, 0.65);
                border-radius: 16px;
                padding: 6px;
            }
            QLabel {
                border: none;
            }
            QSlider {
                border: none;
            }
        """)
        posture_container_layout = QVBoxLayout(posture_container)
        posture_container_layout.setContentsMargins(6, 12, 6, 0)  # Removed bottom padding
        posture_container_layout.setSpacing(2)  # Minimal spacing between toggle and interval

        # Add all the posture settings as before
        posture_layout = QHBoxLayout()
        posture_layout.setSpacing(4)
        posture_label = QLabel("Posture check")
        posture_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                border: none;
            }
        """)
        self.posture_checkbox = ToggleSwitch()
        posture_layout.addWidget(posture_label)
        posture_layout.addWidget(self.posture_checkbox)
        posture_layout.addStretch()
        posture_container_layout.addLayout(posture_layout)

        # Posture timer slider
        posture_timer_layout = QHBoxLayout()
        posture_timer_layout.setSpacing(4)
        posture_timer_layout.setContentsMargins(0, 0, 0, 0)
        posture_timer_label = QLabel("Reminder interval:")
        posture_timer_label.setStyleSheet("border: none;")
        self.posture_timer_slider = QSlider(Qt.Horizontal)
        self.posture_timer_slider.setFixedWidth(150)  # Set fixed width for slider
        self.posture_timer_slider.setMinimum(300)
        self.posture_timer_slider.setMaximum(3600)
        self.posture_timer_slider.setValue(1200)
        self.posture_timer_display = QLabel("20 minutes")
        self.posture_timer_display.setStyleSheet("border: none;")
        self.posture_timer_display.setFixedWidth(80)  # Set fixed width for display label
        self.posture_timer_slider.valueChanged.connect(self.update_posture_timer_display)
        
        posture_timer_layout.addWidget(posture_timer_label)
        posture_timer_layout.addWidget(self.posture_timer_slider)
        posture_timer_layout.addWidget(self.posture_timer_display)
        posture_container_layout.addLayout(posture_timer_layout)

        content_layout.addWidget(posture_container, 0, Qt.AlignCenter)
        content_layout.addSpacing(20)

        # Center the start button
        start_container = QHBoxLayout()
        start_container.setContentsMargins(0, 0, 0, 0)
        start_container.setSpacing(0)
        self.start_btn = QPushButton('Start deskpet')
        self.start_btn.setObjectName("startButton")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.toggle_pet)
        self.start_btn.setFixedSize(360, 64)  # Updated height to 64px
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
        # This method can be removed since sprite selection is hardcoded
        pass

    def update_preview_size(self, size):
        # This method can be removed since it's only called by select_sprite
        # which is no longer used
        pass

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
        
        # Draw the background with opacity and border
        painter.setBrush(QColor(255, 255, 255, 245))  # White at 96% opacity (245/255)
        pen = painter.pen()
        pen.setWidth(1)  # Set border width to 1px
        pen.setColor(QColor(0, 0, 0, 127))  # Semi-transparent black for the border
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect(), 20, 20)

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
                96,  # Fixed size to match preview
                850,  # travel range increased to 850px
                self.hydration_checkbox.isChecked(),
                self.timer_slider.value(),
                self.posture_checkbox.isChecked(),
                self.posture_timer_slider.value()
            )
            self.start_btn.setText("Stop deskpet")
        else:
            # Close the pet
            self.pet.close()
            self.pet = None
            self.start_btn.setText("Start deskpet")

    def update_posture_timer_display(self, value):
        if value < 60:
            self.posture_timer_display.setText(f"{value} seconds")
        else:
            minutes = value // 60
            seconds = value % 60
            if seconds == 0:
                self.posture_timer_display.setText(f"{minutes} minutes")
            else:
                self.posture_timer_display.setText(f"{minutes} min {seconds} sec")

class DesktopPet(QMainWindow):
    def __init__(self, sprite_size, max_travel, hydration_enabled=False, hydration_interval=300, posture_enabled=False, posture_interval=300):
        super().__init__()
        self.sprite_size = sprite_size
        self.max_travel = max_travel
        self.hydration_enabled = hydration_enabled
        self.hydration_interval = hydration_interval
        self.posture_enabled = posture_enabled
        self.posture_interval = posture_interval
        self.start_x = None
        self.reminder_window = ReminderWindow()
        self.posture_reminder_window = ReminderWindow("Posture")
        
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
        
        if self.posture_enabled:
            self.posture_timer = QTimer(self)
            self.posture_timer.timeout.connect(self.posture_check)
            self.posture_timer.start(self.posture_interval * 1000)
        
        self.setGeometry(self.x, self.y, self.sprite_size, self.sprite_size)
        self.show()
        
        if self.start_x is None:
            self.start_x = self.x
    
    def hydration_check(self):
        self.reminder_window.show()
        self.reminder_window.raise_()
        self.reminder_window.activateWindow()
    
    def posture_check(self):
        self.posture_reminder_window.show()
        self.posture_reminder_window.raise_()
        self.posture_reminder_window.activateWindow()
    
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
    
    # Set application icon
    app.setWindowIcon(QIcon('icon.ico'))
    
    selector = SpriteSelector()
    selector.selected_sprite = QPixmap("goose.png")
    selector.start_btn.setEnabled(True)
    
    # Since sprite selection is hardcoded, we can remove this loop
    # and just hide the button directly if needed
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
    
    selector.show()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
