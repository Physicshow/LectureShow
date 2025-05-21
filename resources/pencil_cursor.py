#!/usr/bin/env python3
"""
Pencil-shaped cursor image generation script
Creates the resources/pencil_cursor.png file.
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPainter, QPen, QPixmap, QColor, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QSize, QRect

def create_pencil_cursor():
    """Creates and saves a pencil-shaped cursor image."""
    # Set image size (create large 64x64 pixel image then scale down)
    size = QSize(64, 64)
    
    # Create transparent pixmap
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    # Initialize painter
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Set black outline
    outline_pen = QPen(QColor(0, 0, 0), 2.0)
    outline_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    outline_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(outline_pen)
    
    # White fill color (inside of pencil is white in the image)
    fill_color = QColor(255, 255, 255)
    painter.setBrush(QBrush(fill_color))
    
    # Create pencil outline path
    pencil_path = QPainterPath()
    
    # Start point of pencil path (tip of pencil)
    pencil_path.moveTo(5, 5)  # Pencil tip (hotspot)
    
    # Upper part of pencil (zigzag)
    pencil_path.lineTo(15, 5)
    pencil_path.arcTo(15, 5, 6, 6, 180, -180)  # First curve
    pencil_path.lineTo(25, 11)
    pencil_path.arcTo(25, 9, 6, 6, 180, -180)  # Second curve
    pencil_path.lineTo(35, 15)
    
    # Right sloped side of pencil
    pencil_path.lineTo(55, 35)
    
    # Rounded bottom part of pencil (eraser)
    pencil_path.arcTo(40, 35, 30, 20, 0, 180)
    
    # Left sloped side of pencil
    pencil_path.lineTo(5, 5)  # Return to pencil tip
    
    # Draw pencil outline
    painter.drawPath(pencil_path)
    
    # Draw vertical lines inside pencil
    line_pen = QPen(QColor(0, 0, 0), 1.5)
    painter.setPen(line_pen)
    
    # Vertical line 1
    painter.drawLine(15, 10, 42, 38)
    
    # Vertical line 2
    painter.drawLine(25, 10, 48, 38)
    
    # Vertical line 3
    painter.drawLine(35, 15, 52, 38)
    
    # Horizontal lines (eraser part)
    painter.drawLine(40, 40, 55, 40)
    painter.drawLine(40, 45, 55, 45)
    
    # End painter
    painter.end()
    
    # Scale pixmap to 32x32
    final_pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    # Save pixmap to file
    final_pixmap.save("resources/pencil_cursor.png", "PNG")
    print("Pencil cursor image created: resources/pencil_cursor.png")
    print("Hotspot position: (5, 5) - Located at the pencil tip")

if __name__ == "__main__":
    # QApplication instance required
    app = QApplication([])
    create_pencil_cursor() 