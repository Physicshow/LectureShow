from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QGuiApplication
from .click_effect import ClickEffectWidget
import logging
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)

class ClickEffectManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("Initializing ClickEffectManager")
        
        # Transparent widget that covers the entire screen
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Required setting to detect mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        # Set to full screen
        self.setGeometry(0, 0, 3000, 2000)  # Set to a sufficiently large size
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # Timer for global mouse events
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_mouse_press)
        self.check_timer.start(50)  # Check every 50ms
        
        self.last_cursor_pos = QCursor.pos()
        self.last_button_state = False
        
        self.position = "left"  # Default: bottom left
        
        logger.debug("ClickEffectManager initialized with size: {}x{}".format(self.width(), self.height()))
        
    def check_mouse_press(self):
        # Check current mouse state
        current_pos = QCursor.pos()
        # Get mouse button state (from QGuiApplication)
        current_button_state = QGuiApplication.mouseButtons() & Qt.MouseButton.LeftButton
        
        # If left button pressed now but wasn't pressed before
        if current_button_state and not self.last_button_state:
            logger.debug(f"Mouse press detected at {current_pos}")
            effect = ClickEffectWidget()
            # 설정된 색상 적용
            effect.color = QSettings().value("click_effect/color", QColor(255,255,255), type=QColor)
            effect.show_at(current_pos)
            logger.debug("Click effect created and shown")
            
        # Update state
        self.last_cursor_pos = current_pos
        self.last_button_state = current_button_state

    def mousePressEvent(self, event):
        logger.debug(f"Direct mouse press event in ClickEffectManager at {event.globalPos()}")
        effect = ClickEffectWidget()
        # 설정된 색상 적용
        effect.color = QSettings().value("click_effect/color", QColor(255,255,255), type=QColor)
        effect.show_at(event.globalPos())
        super().mousePressEvent(event)