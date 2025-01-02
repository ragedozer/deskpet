import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QFileDialog, 
                           QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                           QMessageBox, QDialog, QSlider, QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QTransform

class HydrationPopup(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setText("Hydration check!")
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 220);
                padding: 5px;
                border-radius: 5px;
                border: 1px solid gray;
            }
        """)
        self.adjustSize()
        
    def show_above(self, x, y, width):
        self.move(x + width//2 - self.width()//2, y - self.height() - 5)
        self.show()
        # Auto-hide after 3 seconds
        QTimer.singleShot(3000, self.hide)

class SpriteSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.selected_sprite = None
        self.sprite_size = 64
        self.max_travel = 500
        self.hydration_enabled = False
        self.hydration_interval = 300  # Default 5 minutes (300 seconds)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Pet Configuration')
        self.setModal(True)
        
        main_layout = QVBoxLayout()
        
        # Sprite preview section
        self.preview = QLabel()
        self.preview.setFixedSize(128, 128)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("border: 2px dashed gray;")
        main_layout.addWidget(self.preview)
        
        select_btn = QPushButton('Select Sprite Image')
        select_btn.clicked.connect(self.select_sprite)
        main_layout.addWidget(select_btn)
        
        # Size control section
        size_layout = QHBoxLayout()
        size_label = QLabel("Pet Size:")
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(16)
        self.size_slider.setMaximum(256)
        self.size_slider.setValue(64)
        self.size_slider.setTickPosition(QSlider.TicksBelow)
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setMinimum(16)
        self.size_spinbox.setMaximum(256)
        self.size_spinbox.setValue(64)
        
        self.size_slider.valueChanged.connect(self.size_spinbox.setValue)
        self.size_spinbox.valueChanged.connect(self.size_slider.setValue)
        self.size_slider.valueChanged.connect(self.update_preview_size)
        
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_spinbox)
        main_layout.addLayout(size_layout)
        
        # Travel width section
        travel_layout = QHBoxLayout()
        travel_label = QLabel("Max Travel Width:")
        self.travel_spinbox = QSpinBox()
        self.travel_spinbox.setMinimum(100)
        self.travel_spinbox.setMaximum(9999)
        self.travel_spinbox.setValue(500)
        self.travel_spinbox.setSuffix(" pixels")
        
        travel_layout.addWidget(travel_label)
        travel_layout.addWidget(self.travel_spinbox)
        main_layout.addLayout(travel_layout)
        
        # Hydration timer section
        hydration_layout = QVBoxLayout()
        
        # Checkbox for enabling/disabling
        self.hydration_checkbox = QCheckBox("Enable Hydration Timer")
        self.hydration_checkbox.setChecked(False)
        hydration_layout.addWidget(self.hydration_checkbox)
        
        # Timer interval control
        timer_layout = QHBoxLayout()
        timer_label = QLabel("Reminder Interval:")
        self.timer_spinbox = QSpinBox()
        self.timer_spinbox.setMinimum(5)
        self.timer_spinbox.setMaximum(3600)
        self.timer_spinbox.setValue(300)
        self.timer_spinbox.setSuffix(" seconds")
        
        timer_layout.addWidget(timer_label)
        timer_layout.addWidget(self.timer_spinbox)
        hydration_layout.addLayout(timer_layout)
        
        main_layout.addLayout(hydration_layout)
        
        # Start button
        self.start_btn = QPushButton('Start Pet')
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.accept)
        main_layout.addWidget(self.start_btn)
        
        self.setLayout(main_layout)
    
    def update_preview_size(self, size):
        if self.selected_sprite:
            scaled_preview = self.selected_sprite.scaled(
                size, size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview.setPixmap(scaled_preview)
        self.sprite_size = size
    
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
                self.update_preview_size(self.size_slider.value())
                self.start_btn.setEnabled(True)
            else:
                QMessageBox.warning(self, "Error", "Invalid image file!")

class DesktopPet(QMainWindow):
    def __init__(self, sprite_pixmap, sprite_size, max_travel, hydration_enabled=False, hydration_interval=300):
        super().__init__()
        self.sprite_pixmap = sprite_pixmap
        self.sprite_size = sprite_size
        self.max_travel = max_travel
        self.hydration_enabled = hydration_enabled
        self.hydration_interval = hydration_interval
        self.start_x = None
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create sprite container
        self.pet = QLabel(self)
        self.pet.setGeometry(0, 0, self.sprite_size, self.sprite_size)
        
        # Create hydration popup
        self.hydration_popup = HydrationPopup()
        
        # Create sprites
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
        
        # Initialize position
        self.x = 500
        self.y = 500
        self.direction = 1
        self.is_moving = False
        self.is_dragging = False
        self.drag_offset = None
        
        # Set up movement and decision timers
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_position)
        self.move_timer.start(50)
        
        self.decision_timer = QTimer(self)
        self.decision_timer.timeout.connect(self.make_decision)
        self.decision_timer.start(3000)
        
        # Set up hydration timer if enabled
        if self.hydration_enabled:
            self.hydration_timer = QTimer(self)
            self.hydration_timer.timeout.connect(self.hydration_check)
            self.hydration_timer.start(self.hydration_interval * 1000)  # Convert to milliseconds
        
        self.setGeometry(self.x, self.y, self.sprite_size, self.sprite_size)
        self.show()
        
        if self.start_x is None:
            self.start_x = self.x
    
    def hydration_check(self):
        # Show hydration popup above pet
        self.hydration_popup.show_above(self.x, self.y, self.sprite_size)
    
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
            
            # Update hydration popup position if it's visible
            if self.hydration_popup.isVisible():
                self.hydration_popup.show_above(self.x, self.y, self.sprite_size)
    
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
        from PyQt5.QtWidgets import QMenu
        menu = QMenu()
        exit_action = menu.addAction("Exit")
        action = menu.exec_(position)
        
        if action == exit_action:
            QApplication.quit()

def main():
    app = QApplication(sys.argv)
    
    # Create and show the sprite selector dialog
    selector = SpriteSelector()
    if selector.exec_() == QDialog.Accepted and selector.selected_sprite is not None:
        # Create pet with all configuration options
        pet = DesktopPet(
            selector.selected_sprite,
            selector.sprite_size,
            selector.travel_spinbox.value(),
            selector.hydration_checkbox.isChecked(),
            selector.timer_spinbox.value()
        )
        return app.exec_()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
