from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QSize, QTimer, pyqtProperty, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen
import logging

logger = logging.getLogger(__name__)

class ClickEffectWidget(QWidget):
    def __init__(self, parent=None, is_drag=False):
        super().__init__(parent)
        logger.debug("Initializing ClickEffectWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        
        # Set drag mode
        self.is_drag = is_drag
        self.is_complete = False
        
        # Set animation properties
        self._size = 10
        self._opacity = 1.0
        self._max_size = 150.0
        self._half_size = self._max_size * 0.5
        
        # Circle color (default: white)
        self._color = QColor(255, 255, 255)
        
        # Set initial widget size
        self.setFixedSize(300, 300)
        
        # Configure animations
        self.size_animation = QPropertyAnimation(self, b"circle_size")
        self.opacity_animation = QPropertyAnimation(self, b"opacity")
        
        # Timer to remove widget after animation completes
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.setSingleShot(True)
        self.cleanup_timer.timeout.connect(self.deleteLater)
        logger.debug("ClickEffectWidget initialized")
    
    # Property for circle size
    @pyqtProperty(float)
    def circle_size(self):
        return self._size
    
    @circle_size.setter
    def circle_size(self, size):
        self._size = size
        self.update()  # Refresh widget
    
    # Property for opacity
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, opacity):
        self._opacity = opacity
        self.update()  # Refresh widget
    
    # Property for color
    @pyqtProperty(QColor)
    def color(self):
        return self._color
    
    @color.setter
    def color(self, color):
        self._color = color
        self.update()  # Refresh widget
        
    def show_at(self, pos):
        logger.debug(f"Showing effect at position: {pos}")
        # Position widget (centered)
        self.move(pos.x() - self.width()//2, pos.y() - self.height()//2)
        
        # Play full animation when not in drag mode
        if not self.is_drag:
            self._start_full_animation()
        else:
            self._start_half_animation()
        
    def _start_full_animation(self):
        # Configure size animation
        self.size_animation.setDuration(400)
        self.size_animation.setStartValue(10.0)
        self.size_animation.setEndValue(self._max_size)
        self.size_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Configure opacity animation
        self.opacity_animation.setDuration(400)
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start animations
        self.show()
        self.size_animation.start()
        self.opacity_animation.start()
        logger.debug("Full effect animations started")
        
        # Remove widget after animation completes
        self.cleanup_timer.start(450)
    
    def _start_half_animation(self):
        # Configure size animation for half progress
        self.size_animation.setDuration(200)
        self.size_animation.setStartValue(10.0)
        self.size_animation.setEndValue(self._half_size)
        self.size_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Configure opacity animation for half progress
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.5)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start animations
        self.show()
        self.size_animation.start()
        self.opacity_animation.start()
        logger.debug("Half effect animations started")
    
    def update_position(self, pos):
        """Update position during drag"""
        if self.is_drag and not self.is_complete:
            self.move(pos.x() - self.width()//2, pos.y() - self.height()//2)
    
    def complete_animation(self, pos):
        """Run remaining animation when drag completes"""
        if self.is_drag and not self.is_complete:
            self.is_complete = True
            self.move(pos.x() - self.width()//2, pos.y() - self.height()//2)
            
            # Run the second half of the animation
            self.size_animation.setDuration(200)
            self.size_animation.setStartValue(self._half_size)
            self.size_animation.setEndValue(self._max_size)
            self.size_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            self.opacity_animation.setDuration(200)
            self.opacity_animation.setStartValue(0.5)
            self.opacity_animation.setEndValue(0.0)
            self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            self.size_animation.start()
            self.opacity_animation.start()
            logger.debug("Completing drag animation")
            
            # Remove widget after animation completes
            self.cleanup_timer.start(250)
        
    def paintEvent(self, event):
        # Excessive logging removed
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circle with the configured color
        pen = QPen(self._color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setOpacity(self._opacity)
        
        # Calculate circle center and radius
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = self._size
        
        # Draw circle (starting from center)
        painter.drawEllipse(
            int(center_x - radius), 
            int(center_y - radius), 
            int(radius * 2), 
            int(radius * 2)
        )