import logging
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer, pyqtProperty, QEasingCurve, QPoint, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath

logger = logging.getLogger(__name__)

class ScrollEffectWidget(QWidget):
    def __init__(self, parent=None, direction="up"):
        super().__init__(parent)
        # self.pixel_ratio = QApplication.primaryScreen().devicePixelRatioF() # Removed
        self.pixel_ratio = 1.0 # Default value
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        
        # Scroll direction (up or down)
        self.direction = direction
        
        # Animation properties
        self._opacity = 1.0
        self._dot_position = 0.0  # Position of inner circle (0.0 ~ 1.0)
        
        # Chevron arrow properties
        self._arrow_opacity = 0.0
        
        # Widget size setting (increased height for arrow margin)
        self.setFixedSize(44, 110)  # Slightly increased width and height
        
        # Animation setup
        self.opacity_animation = QPropertyAnimation(self, b"opacity")
        self.dot_animation = QPropertyAnimation(self, b"dot_position")
        self.arrow_animation = QPropertyAnimation(self, b"arrow_opacity")
        
        # Timer for removing widget after animation completion
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.setSingleShot(True)
        self.cleanup_timer.timeout.connect(self.deleteLater)
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, opacity):
        self._opacity = opacity
        self.update()
    
    @pyqtProperty(float)
    def dot_position(self):
        return self._dot_position
    
    @dot_position.setter
    def dot_position(self, position):
        self._dot_position = position
        self.update()
    
    @pyqtProperty(float)
    def arrow_opacity(self):
        return self._arrow_opacity
    
    @arrow_opacity.setter
    def arrow_opacity(self, opacity):
        self._arrow_opacity = opacity
        self.update()
    
    def show_at(self, pos):
        """Display the scroll effect."""
        current_screen = QApplication.instance().primaryScreen()
        if current_screen:
            self.pixel_ratio = current_screen.devicePixelRatio()
        else:
            logger.warning("ScrollEffectWidget: Could not get primary screen information. Using default pixel_ratio=1.0")
            self.pixel_ratio = 1.0 
            
        # pos is assumed to be in physical pixels
        logical_x = pos.x() / self.pixel_ratio
        logical_y = pos.y() / self.pixel_ratio

        # Define a fixed logical offset (e.g., 30 pixels to the right)
        desired_logical_offset_x = 30
        
        # Calculate the final logical position for the widget's top-left corner
        # The widget's height (self.height()) is assumed to be in logical pixels as set by setFixedSize
        final_logical_x = logical_x + desired_logical_offset_x
        final_logical_y = logical_y - (self.height() / 2)

        self.move(int(final_logical_x), int(final_logical_y))
        
        # Fade in/out animation
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setKeyValueAt(0.3, 1.0)  # Fully opaque at 30% point
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Inner circle movement animation
        self.dot_animation.setDuration(500)
        if self.direction == "up":
            self.dot_animation.setStartValue(0.1)  # Bottom start position (0.1)
            self.dot_animation.setEndValue(0.9)    # Top end position (0.9)
        else:
            self.dot_animation.setStartValue(0.9)  # Top start position (0.9)
            self.dot_animation.setEndValue(0.1)    # Bottom end position (0.1)
            
        # Arrow animation
        self.arrow_animation.setDuration(500)
        self.arrow_animation.setStartValue(0.0)
        self.arrow_animation.setKeyValueAt(0.3, 1.0)
        self.arrow_animation.setEndValue(0.8)
        
        self.dot_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.arrow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start animation
        self.show()
        self.opacity_animation.start()
        self.dot_animation.start()
        self.arrow_animation.start()
        
        # Remove widget after animation completion
        self.cleanup_timer.start(550)
    
    def _draw_chevron(self, painter, x, y, width, is_up, opacity):
        """Draw a chevron arrow."""
        if opacity <= 0:
            return
            
        # Calculate arrow size and thickness (enlarged 2x)
        arrow_width = int(width * 1.2)
        arrow_height = int(width * 0.6)
        stroke_width = 3  # Changed to integer
        
        # Save original opacity
        original_opacity = painter.opacity()
        painter.setOpacity(original_opacity * opacity)
        
        # Set arrow pen - changed to translucent white
        pen = QPen(QColor(255, 255, 255, 180))  # Alpha value 180 (approx. 70% opacity)
        pen.setWidth(stroke_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Set arrow internal fill color - very light translucent white
        painter.setBrush(QBrush(QColor(255, 255, 255, 20)))  # Alpha value 20 (approx. 8% opacity)
        
        # Create arrow path
        path = QPainterPath()
        if is_up:
            # Upward arrow
            path.moveTo(x - arrow_width/2, y + arrow_height/2)
            path.lineTo(x, y - arrow_height/2)
            path.lineTo(x + arrow_width/2, y + arrow_height/2)
        else:
            # Downward arrow
            path.moveTo(x - arrow_width/2, y - arrow_height/2)
            path.lineTo(x, y + arrow_height/2)
            path.lineTo(x + arrow_width/2, y - arrow_height/2)
        
        # Draw arrow
        painter.drawPath(path)
        
        # Restore opacity
        painter.setOpacity(original_opacity)
    
    def paintEvent(self, event):
        """Draw the scroll effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        
        # Calculate capsule area (add top and bottom margins)
        arrow_margin = 25  # Increased top/bottom margin for arrows
        capsule_top = arrow_margin
        capsule_height = self.height() - 2 * arrow_margin
        capsule_rect = self.rect().adjusted(6, capsule_top, -6, -(arrow_margin))
        
        # Draw outer capsule shape
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(2)
        painter.setPen(pen)
        # Fill capsule with translucent white
        painter.setBrush(QBrush(QColor(255, 255, 255, 40)))  # Alpha value 40 (approx. 15% opacity)
        painter.drawRoundedRect(capsule_rect, capsule_rect.width() // 2, capsule_rect.width() // 2)
        
        # Draw inner circle - changed to slightly darker blue
        painter.setBrush(QBrush(QColor(150, 200, 255, 180)))  # Alpha value 180 (approx. 70% opacity)
        
        # Calculate capsule top/bottom margins (to prevent circle from exceeding capsule)
        dot_radius = capsule_rect.width() // 4  # Circle radius
        top_margin = capsule_rect.width() // 2  # Top margin (rounded part of capsule)
        bottom_margin = capsule_rect.width() // 2  # Bottom margin (rounded part of capsule)
        
        # Movable height area for the circle
        movable_height = capsule_rect.height() - top_margin - bottom_margin
        
        # Calculate Y position of circle (convert _dot_position in range 0.1~0.9 to actual pixel position)
        dot_y = int(capsule_rect.top() + top_margin + (1.0 - self._dot_position) * movable_height)
        
        # Set X position of circle to center of capsule (1 pixel adjustment)
        dot_x = capsule_rect.center().x() + 1
        
        # Draw circle
        painter.drawEllipse(QPoint(dot_x, dot_y), dot_radius, dot_radius)
        
        # Draw only the opposite direction arrow based on scroll direction
        center_x = self.width() // 2
        
        if self.direction == "up":
            # When scrolling down, show upward arrow only
            # Adjust arrow position with safe margin
            top_y1 = 12
            top_y2 = 20
            self._draw_chevron(painter, center_x, top_y1, int(capsule_rect.width() // 1.5), True, self._arrow_opacity)
            self._draw_chevron(painter, center_x, top_y2, int(capsule_rect.width() // 1.8), True, self._arrow_opacity)
        else:
            # When scrolling up, show downward arrow only
            # Adjust arrow position with safe margin
            bottom_y1 = self.height() - 20
            bottom_y2 = self.height() - 12
            self._draw_chevron(painter, center_x, bottom_y1, int(capsule_rect.width() // 1.8), False, self._arrow_opacity)
            self._draw_chevron(painter, center_x, bottom_y2, int(capsule_rect.width() // 1.5), False, self._arrow_opacity) 
