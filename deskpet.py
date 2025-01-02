import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QFileDialog, 
                           QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                           QMessageBox, QDialog, QSlider, QCheckBox, QMenu)
from PyQt5.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QTransform

# Hide console window
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class ReminderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        self.setWindowTitle("Reminder")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        label = QLabel("Hydration check")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.hide)
        layout.addWidget(ok_button)
        
        self.setFixedSize(200, 100)

class SpriteSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.selected_sprite = None
        self.sprite_size = 65
        # Remove help button from window
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Pet Configuration')
        self.setModal(True)
        self.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        # Container for centered preview
        preview_container = QHBoxLayout()
        preview_container.addStretch()
        
        # Preview section
        self.preview = QLabel()
        self.preview.setFixedSize(128, 128)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("""
            QLabel {
                border: 2px dashed gray;
                background-color: rgba(255, 255, 255, 150);
            }
        """)
        preview_container.addWidget(self.preview)
        preview_container.addStretch()
        layout.addLayout(preview_container)
        
        # Image selection
        select_container = QHBoxLayout()
        select_container.addStretch()
        select_btn = QPushButton('Select Sprite Image')
        select_btn.clicked.connect(self.select_sprite)
        select_container.addWidget(select_btn)
        select_container.addStretch()
        layout.addLayout(select_container)
        
        # Add some space
        layout.addSpacing(10)
        
        # Size control
        size_layout = QHBoxLayout()
        size_label = QLabel("Pet Size:")
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(1)
        self.size_slider.setMaximum(100)
        self.size_slider.setValue(1)
        self.size_display = QLabel("65")
        self.size_display.setMinimumWidth(30)
        
        self.size_slider.valueChanged.connect(self.update_size_from_slider)
        
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_display)
        layout.addLayout(size_layout)
        
        # Travel range
        travel_layout = QHBoxLayout()
        travel_label = QLabel("Travel Range:")
        self.travel_slider = QSlider(Qt.Horizontal)
        self.travel_slider.setMinimum(50)
        self.travel_slider.setMaximum(500)
        self.travel_slider.setValue(250)
        self.travel_display = QLabel("250")
        self.travel_display.setMinimumWidth(30)
        
        self.travel_slider.valueChanged.connect(self.update_travel_display)
        
        travel_layout.addWidget(travel_label)
        travel_layout.addWidget(self.travel_slider)
        travel_layout.addWidget(self.travel_display)
        layout.addLayout(travel_layout)
        
        # Hydration timer
        hydration_layout = QVBoxLayout()
        self.hydration_checkbox = QCheckBox("Enable hydration reminder")
        self.hydration_checkbox.setChecked(False)
        self.hydration_checkbox.stateChanged.connect(self.update_hydration_label)
        hydration_layout.addWidget(self.hydration_checkbox)
        
        timer_layout = QHBoxLayout()
        timer_label = QLabel("Reminder Interval:")
        self.timer_slider = QSlider(Qt.Horizontal)
        self.timer_slider.setMinimum(5)
        self.timer_slider.setMaximum(3600)
        self.timer_slider.setValue(300)
        self.timer_display = QLabel("5 minutes")
        self.timer_display.setMinimumWidth(80)
        
        self.timer_slider.valueChanged.connect(self.update_timer_display)
        
        timer_layout.addWidget(timer_label)
        timer_layout.addWidget(self.timer_slider)
        timer_layout.addWidget(self.timer_display)
        hydration_layout.addLayout(timer_layout)
        
        layout.addLayout(hydration_layout)
        
        # Add some space before the start button
        layout.addSpacing(10)
        
        # Start button in container for centering
        start_container = QHBoxLayout()
        start_container.addStretch()
        self.start_btn = QPushButton('Start Pet')
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.accept)
        start_container.addWidget(self.start_btn)
        start_container.addStretch()
        layout.addLayout(start_container)
        
        self.setLayout(layout)
    
    def update_size_from_slider(self, value):
        actual_size = 65 + (value - 1) * (65/99)
        self.sprite_size = int(actual_size)
        self.size_display.setText(str(self.sprite_size))
        if self.selected_sprite:
            self.update_preview_size(self.sprite_size)
    
    def update_travel_display(self, value):
        self.travel_display.setText(str(value))
    
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
    
    def update_hydration_label(self, state):
        text = "Disable hydration reminder" if state == Qt.Checked else "Enable hydration reminder"
        self.hydration_checkbox.setText(text)
    
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

class DesktopPet(QMainWindow):
    def __init__(self, sprite_pixmap, sprite_size, max_travel, hydration_enabled=False, hydration_interval=300):
        super().__init__()
        self.sprite_pixmap = sprite_pixmap
        self.sprite_size = sprite_size
        self.max_travel = max_travel
        self.hydration_enabled = hydration_enabled
        self.hydration_interval = hydration_interval
        self.start_x = None
        self.reminder_window = ReminderWindow()
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.pet = QLabel(self)
        self.pet.setGeometry(0, 0, self.sprite_size, self.sprite_size)
        
        base_sprite = self.sprite_pixmap.scaled(
            self.sprite_size, self.sprite_size, 
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        transform = QTransform()
        transform.scale(-1, 1)
        mirrored_sprite = base_sprite.transformed(transform)
        
        self.sprites = {
            'idle': base_sprite,
            'walk_right': base_sprite,
            'walk_left': mirrored_sprite
        }
        
        self.current_sprite = 'idle'
        self.pet.setPixmap(self.sprites[self.current_sprite])
        
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
    
    def update_position(self):
        if self.is_moving and not self.is_dragging:
            self.x += 2 * self.direction
            
            self.current_sprite = 'walk_right' if self.direction > 0 else 'walk_left'
            
            if abs(self.x - self.start_x) > self.max_travel // 2:
                if self.x > self.start_x:
                    self.x = self.start_x + self.max_travel // 2
                    self.direction = -1
                else:
                    self.x = self.start_x - self.max_travel // 2
                    self.direction = 1
            
            self.move(self.x, self.y)
            self.pet.setPixmap(self.sprites[self.current_sprite])
    
    def make_decision(self):
        import random
        self.is_moving = random.choice([True, False])
        if not self.is_moving:
            self.current_sprite = 'idle'
            self.pet.setPixmap(self.sprites[self.current_sprite])
        else:
            self.direction = random.choice([-1, 1])
    
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
        self.current_sprite = 'idle'
        self.pet.setPixmap(self.sprites[self.current_sprite])
    
    def show_context_menu(self, position):
        menu = QMenu()
        exit_action = menu.addAction("Exit")
        action = menu.exec_(position)
        
        if action == exit_action:
            QApplication.quit()

def main():
    app = QApplication(sys.argv)
    
    selector = SpriteSelector()
    if selector.exec_() == QDialog.Accepted and selector.selected_sprite is not None:
        pet = DesktopPet(
            selector.selected_sprite,
            selector.sprite_size,
            selector.travel_slider.value(),
            selector.hydration_checkbox.isChecked(),
            selector.timer_slider.value()
        )
        return app.exec_()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
