from PyQt6.QtWidgets import QMainWindow, QWidget, QMenu, QSystemTrayIcon, QDialog, QMessageBox
from PyQt6.QtCore import Qt, QPoint, QSettings, QTimer
from PyQt6.QtGui import QColor, QKeyEvent, QIcon, QPen
from src.input.input_listener import InputListener
from src.ui.overlay_widget import OverlayWidget
from src.ui.click_effect import ClickEffectWidget
from src.ui.scroll_effect import ScrollEffectWidget
from src.ui.zoom_view import ZoomView
from src.ui.circle_cursor import CircleCursor
import logging
from PyQt6.QtWidgets import QApplication

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LectureShow")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Drag effect related variables
        self.drag_effects = {}  # Store effects by button type (left, right)
        
        # Initialize zoom view (not displayed yet)
        self.zoom_view = None
        
        # Initialize circular cursor
        self.circle_cursor = CircleCursor()
        
        # Variables to save original circular cursor properties
        self.original_circle_cursor_size = self.circle_cursor.size
        self.original_circle_cursor_color = self.circle_cursor.color
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create overlay widget for displaying key presses (no parent)
        self.overlay = OverlayWidget()
        
        # Initialize input listener
        self.input_listener = InputListener()
        self.input_listener.input_detected.connect(self.handle_input)
        self.input_listener.position_changed.connect(self.overlay.set_position)
        
        # Connect mouse event signals
        self.input_listener.mouse_clicked.connect(self.show_click_effect)
        self.input_listener.mouse_down.connect(self.on_mouse_down)
        self.input_listener.mouse_move.connect(self.on_mouse_move)
        self.input_listener.mouse_up.connect(self.on_mouse_up)
        
        # Connect scroll effect and modifier key display signals
        self.input_listener.scroll_effect.connect(self.show_scroll_effect)
        self.input_listener.show_modifier.connect(self.overlay.show_input)
        
        # Connect zoom view activation signal
        self.input_listener.activate_zoom.connect(self.activate_zoom_view)
        
        # Connect circular cursor toggle signal
        self.input_listener.toggle_circle_cursor.connect(self.toggle_circle_cursor)
        
        # Connect circular cursor resize signals
        self.input_listener.increase_circle_cursor.connect(self.increase_circle_cursor)
        self.input_listener.decrease_circle_cursor.connect(self.decrease_circle_cursor)
        
        self.input_listener.start()
        
        # Set up system tray icon
        self.setup_tray_icon()
        
        # Redefine exit event for cleanup on system shutdown
        app = QApplication.instance()
        app.aboutToQuit.connect(self.cleanup)
        
        # Set initial position
        self.resize(400, 300)
        self.move_to_bottom_right()
        
        # Hide window (minimize to system tray)
        self.hide()
        self.load_settings()
        logger.info("Main window initialized")
        
    def setup_tray_icon(self):
        """Set up system tray icon"""
        # Create icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set icon image
        icon = QIcon("resources/app_icon.ico")
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)
        
        # Create tray icon menu
        tray_menu = QMenu()
        
        # Open settings window
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)

        # Open help window
        help_action = tray_menu.addAction("Help")
        help_action.triggered.connect(self.open_help)

        tray_menu.addSeparator()
        # Show/hide window action
        toggle_action = tray_menu.addAction("Show/Hide Window")
        toggle_action.triggered.connect(self.toggle_window)
        
        # Add menu separator
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.close_application)
        
        # Set menu
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connect tray icon click event
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # Show tray icon
        self.tray_icon.show()
        
        # Set tooltip
        self.tray_icon.setToolTip("LectureShow")
    
    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation (clicks)"""
        # Toggle window visibility on left click
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window()
    
    def toggle_window(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
            self.activateWindow()
    
    def close_application(self):
        """Exit application"""
        QApplication.quit()
    
    def cleanup(self):
        """Clean up resources on application exit"""
        # Add resource cleanup code if needed
        if self.circle_cursor:
            self.circle_cursor.deleteLater()
        
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
    
    def closeEvent(self, event):
        """Handle window close event - minimize to system tray"""
        # Check if application is actually exiting
        if QApplication.instance().isSavingSession() or QApplication.instance().aboutToQuit.isConnected():
            event.accept()
        else:
            # Hide window and ignore event
            self.hide()
            event.ignore()
    
    def show_click_effect(self, x, y):
        logger.debug(f"Creating click effect at ({x}, {y})")
        effect = ClickEffectWidget()
        # 설정된 색상 적용
        effect.color = QSettings().value("click_effect/color", QColor(255,255,255), type=QColor)
        effect.show_at(QPoint(x, y))
        logger.debug("Click effect created and shown")
        
    def show_scroll_effect(self, x, y, direction):
        """Display scroll effect."""
        logger.debug(f"Creating scroll effect at ({x}, {y}), direction: {direction}")
        effect = ScrollEffectWidget(direction=direction)
        effect.show_at(QPoint(x, y))
        logger.debug("Scroll effect created and shown")
        
    def on_mouse_down(self, x, y, button_type):
        logger.debug(f"Mouse {button_type} down at ({x}, {y})")
        # Start drag - create drag effect
        self.drag_effects[button_type] = ClickEffectWidget(is_drag=True)
        # 설정된 색상 적용
        self.drag_effects[button_type].color = QSettings().value("click_effect/color", QColor(255,255,255), type=QColor)
        self.drag_effects[button_type].show_at(QPoint(x, y))
        logger.debug(f"Drag effect for {button_type} created and shown")
        
    def on_mouse_move(self, x, y):
        # During drag - update effect position
        for effect in self.drag_effects.values():
            if effect:
                effect.update_position(QPoint(x, y))
        
        # Update circular cursor position - always perform
        if self.circle_cursor and self.circle_cursor.isVisible():
            # Update with actual mouse position instead of QPoint
            self.circle_cursor.update_position()
            # Excessive logging removed
        
    def on_mouse_up(self, x, y, button_type):
        logger.debug(f"Mouse {button_type} up at ({x}, {y})")
        # End drag - complete effect
        if button_type in self.drag_effects and self.drag_effects[button_type]:
            self.drag_effects[button_type].complete_animation(QPoint(x, y))
            self.drag_effects[button_type] = None
            logger.debug(f"Drag effect for {button_type} completed")
    
    def handle_input(self, key_combo):
        """Handle key input."""
        # Display key input on overlay
        self.overlay.show_input(key_combo)
        
        # Process shortcuts
        key_combo_lower = key_combo.lower()
        
        # Activate capture mode (Ctrl+1)
        if key_combo_lower == "ctrl+1":
            logger.debug("handle_input - Ctrl+1 capture mode activation detected")
            # 1) Hide subtitle
            if self.overlay.isVisible():
                logger.debug("Hiding overlay before capture")
                self.overlay.hide()
                QApplication.processEvents()
            # 2) Start zoom view
            self.activate_zoom_view()
            return
            
        # Circular cursor size adjustment - Ctrl+Shift+key combinations
        if key_combo_lower in ["ctrl+shift++", "ctrl+shift+="] and self.circle_cursor:
            logger.debug(f"Circular cursor size increase shortcut detected: {key_combo}")
            self.increase_circle_cursor()
        elif key_combo_lower == "ctrl+shift+-" and self.circle_cursor:
            logger.debug(f"Circular cursor size decrease shortcut detected: {key_combo}")
            self.decrease_circle_cursor()
        elif key_combo_lower == "alt+c" and self.circle_cursor:
            logger.debug(f"Circular cursor toggle shortcut detected: {key_combo}")
            self.toggle_circle_cursor()
            
    def toggle_circle_cursor(self):
        """Toggle circular cursor visibility"""
        logger.debug("Toggling circle cursor visibility")
        if self.circle_cursor:
            self.circle_cursor.toggle_visibility()
            
    def increase_circle_cursor(self):
        """Increase circular cursor size"""
        logger.debug("Increasing circle cursor size")
        if self.circle_cursor:
            self.circle_cursor.increase_size()
            
    def decrease_circle_cursor(self):
        """Decrease circular cursor size"""
        logger.debug("Decreasing circle cursor size")
        if self.circle_cursor:
            self.circle_cursor.decrease_size()
            
    def activate_zoom_view(self):
        """Activate zoom view."""
        logger.debug("Activating zoom view")
        
        # Ignore if already active
        if self.zoom_view is not None and self.zoom_view.isVisible():
            logger.debug("Zoom view already active")
            return
        
        try:
            # Create zoom view
            self.zoom_view = ZoomView()
            self.zoom_view.main_window_overlay = self.overlay
            
            # Transfer current circular cursor settings
            if self.circle_cursor:
                # Save current circular cursor size and color
                self.original_circle_cursor_size = self.circle_cursor.size
                self.original_circle_cursor_color = self.circle_cursor.color
                
                # Transfer circular cursor size and color
                self.zoom_view.circle_cursor_size = self.circle_cursor.size
                self.zoom_view.circle_cursor_color = self.circle_cursor.color
                
                # Remember current circular cursor visibility state
                cursor_was_visible = self.circle_cursor.isVisible()
                self.zoom_view.circle_cursor_was_visible = cursor_was_visible
                
                # Only transfer if circular cursor is not visible
                if not cursor_was_visible:
                    self.zoom_view.circle_cursor_size = 0
                    
                # Directly pass circular cursor object to ZoomView
                self.zoom_view.main_window_circle_cursor = self.circle_cursor
            
            # 성능 개선: 신호 연결 전에 모든 설정 완료
            self.zoom_view.closed.connect(self.on_zoom_view_closed)
            
            # 화면 활성화 - 다른 작업은 내부에서 지연 처리됨
            self.zoom_view.activate()
            
            # 원래 커서 숨기기 - 작업이 준비된 후에 실행
            QTimer.singleShot(200, self._hide_cursor_after_zoom_active)
            
        except Exception as e:
            logger.error(f"Zoom view activation failed: {e}")
            
            # 오류 발생 시 정리
            if hasattr(self, 'zoom_view') and self.zoom_view:
                try:
                    self.zoom_view = None
                except:
                    pass

    def _hide_cursor_after_zoom_active(self):
        """그리기 모드가 활성화된 후 커서 숨기기"""
        if self.circle_cursor and self.zoom_view and self.zoom_view.isVisible():
            self.circle_cursor.hide()
            logger.debug("Main window circle cursor hidden for zoom view")

    def on_zoom_view_closed(self):
        """Method called when zoom view is closed"""
        logger.debug("Zoom view closed")
        
        # Get updated circular cursor size and color from ZoomView
        if self.zoom_view and self.circle_cursor:
            # Update circular cursor size if new size exists
            zoom_view_cursor_size = self.zoom_view.circle_cursor_size
            if zoom_view_cursor_size > 0:
                # Save changes made in ZoomView
                self.original_circle_cursor_size = zoom_view_cursor_size
                self.original_circle_cursor_color = self.zoom_view.circle_cursor_color
            
            # Restore circular cursor to original settings
            self.circle_cursor.size = self.original_circle_cursor_size
            self.circle_cursor.color = self.original_circle_cursor_color
            
            # Force circular cursor to show (workaround for issue)
            self.circle_cursor.show()
            logger.debug(f"Circle cursor FORCED to show at size {self.original_circle_cursor_size}")
            
            # Force UI state update
            QApplication.processEvents()
        else:
            logger.debug("No zoom view or circle cursor reference found")
        
        # Remove zoom view reference
        self.zoom_view = None

    def keyPressEvent(self, event):
        # ESC: Close zoom view only
        if event.key() == Qt.Key.Key_Escape and self.zoom_view:
            self.zoom_view.close_zoom_view()
            event.accept()
            return
        
        # 포커스 확인 로깅 추가
        # Add focus check logging
        
        # 나머지 키 이벤트 처리
        # Process remaining key events
        
        # 지우개 모드에서 +/- 키로 크기 조절
        # Adjust size with +/- keys in eraser mode
        
        # - 키만 누를 경우: 현재 활성 도구의 크기 감소
        # When only - key is pressed: decrease size of current active tool
        
        # R: Reset view (panning offset 및 zoom factor 초기화)
        # R: Reset view (initialize panning offset and zoom factor)
        
        # 그 외: 기본 처리
        # Others: Default processing
        
        super().keyPressEvent(event)

    def move_to_bottom_right(self):
        """Move window to bottom right of screen"""
        screen = self.screen().availableGeometry()
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 20) 

    def open_settings(self):
        from src.ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        dlg.exec()  # Modal execution: settings apply immediately

    def open_help(self):
        text = (
            "<b>LectureShow</b><br>"
            "Physicshow screen capture & drawing tool<br><br>"
            
            "<b>일반 단축키</b><br>"
            "• Ctrl+1: 화면 캡처 및 그리기 모드 진입<br>"
            "• Ctrl+Shift+'+' : 원형 커서 크기 증가<br>"
            "• Ctrl+Shift+'-' : 원형 커서 크기 감소<br>"
            "• ESC: 그리기 모드 종료<br><br>"
            
            "<b>그리기 모드 단축키</b><br>"
            "<i>색상 단축키</i><br>"
            "• 1: 펜 색상 1 선택 (기본: 빨강)<br>"
            "• 2: 펜 색상 2 선택 (기본: 초록)<br>"
            "• 3: 펜 색상 3 선택 (기본: 파랑)<br>"
            "• 4: 하이라이트 색상 1 선택 (기본: 노랑)<br>"
            "• 5: 하이라이트 색상 2 선택 (기본: 연두색)<br>"
            "• 6: 하이라이트 색상 3 선택 (기본: 분홍)<br><br>"
            
            "<i>도구 크기 조절</i><br>"
            "• '+' : 현재 선택된 도구 두께 증가<br>"
            "• '-' : 현재 선택된 도구 두께 감소<br><br>"
            
            "<i>확대/축소 및 이동</i><br>"
            "• Ctrl+'+' : 확대<br>"
            "• Ctrl+'-' : 축소<br>"
            "• Shift+마우스 왼쪽 버튼 드래그: 화면 이동(패닝)<br>"
            "• R: 뷰 리셋 (원래 크기 및 위치로 복원)<br><br>"
            
            "<i>도구 사용법</i><br>"
            "• 마우스 왼쪽 버튼 클릭/드래그: 펜으로 그리기<br>"
            "• 마우스 오른쪽 버튼 클릭/드래그: 하이라이터로 그리기<br>"
            "• 마우스 왼쪽+오른쪽 버튼 동시 드래그: 지우개 모드<br>"
            "• 지우개 모드에서 '+'/'-' : 지우개 크기 조절<br><br>"
            
            "<b>설정 옵션</b><br>"
            "• 펜 및 하이라이트 색상: 설정 창에서 사용자 지정 가능<br>"
            "• 펜 및 하이라이트 두께: 설정 창에서 조절 가능<br>"
            "<b>Shortcuts</b><br>"
            "[Ctrl]+[1]: Capture & Zoom mode<br>"
            "[Ctrl]+[Shift]+[+]/[-] : Adjust circular cursor size<br>"
            "[ESC]: Close Zoom mode<br><br>"
            "<b>Drawing Mode Shortcuts</b><br>"
            "[1]/[2]/[3]: Change pen color (Red/Green/Blue)<br>"
            "[4]/[5]/[6]: Change highlighter color (Yellow/Light Green/Pink)<br>"
            "[+]/[-] : Adjust pen/highlighter thickness<br>"
            "[Shift]+[Left Click]: Pan mode<br>"
            "[Left Click]: Draw with pen<br>"
            "[Right Click]: Draw with highlighter<br>"
            "[Left Click]+[Right Click]: Eraser mode<br>"
            "<b>Communication</b><br>"
            "GitHub: hhttps://github.com/Physicshow/LectureShow/releases/latest"
        )
        QMessageBox.information(self, "Help", text)

    def load_settings(self):
        s = QSettings()
        
        # Circular cursor color - ZoomView와 관계없이 항상 적용
        col = s.value("cursor/color", QColor(0,120,215), type=QColor)
        if self.circle_cursor:
            self.circle_cursor.color = col  # color setter에서 불투명도 자동 적용
        
        # Apply settings only if ZoomView has been created
        if self.zoom_view:
            # Pen thickness
            self.zoom_view.pen_width = s.value("pen/width", 3, int)
            
            # Highlight opacity
            alpha = s.value("highlight/opacity", 64, int)
            self.zoom_view.highlighter_color.setAlpha(alpha)
            
            # Highlight width
            self.zoom_view.highlighter_width = s.value("highlight/width", 20, int)
            
            # Highlight color
            hl_color = s.value("highlight/color", QColor(255,255,0,64), type=QColor)
            self.zoom_view.highlighter_color = hl_color
            
            # Highlight opacity
            alpha = s.value("highlight/opacity", 64, int)
            self.zoom_view.highlighter_color.setAlpha(alpha)
            
            # Circular cursor color
            self.zoom_view.circle_cursor_color = col
            
            # Subtitle font size & background color
            fs = s.value("subtitle/fontsize", 50, int)
            bgcol = s.value("subtitle/bgcolor", QColor(60,60,60,217), type=QColor)
            
            # Update OverlayWidget internal properties
            OverlayWidget.FONT_SIZE = fs
            OverlayWidget.CARD_BG = bgcol.name(QColor.HexArgb)

    def erase_at_position(self, pos):
        """Erase drawing at specified position"""
        # Convert screen coordinates to image coordinates
        image_pos = self.screen_to_image(pos)
        
        # Calculate eraser size considering current zoom/scale ratio
        scaled_eraser_size = self.eraser_size / self.scale_factor
        
        # Calculate eraser area (in image coordinates)
        eraser_rect = QRect(...)

        # Find drawings to erase
        to_remove = []
        for i, (start_pt, end_pt, col, wd) in enumerate(self.drawings):
            # Calculate line bounding box (in image coordinates)
            line_rect = QRect(...)
            
            # Add to removal list if eraser area intersects with line
            if eraser_rect.intersects(line_rect):
                to_remove.append(i)
        
        # Remove from back to front (to prevent index changes)
        for i in sorted(to_remove, reverse=True):
            del self.drawings[i]
        
        # Check and remove highlighter paths too
        to_remove = []
        for i, path_info in enumerate(self.highlighter_paths):
            # Convert highlighter path bounding box to image coordinates
            path_rect = path_info['path'].boundingRect()
            scaled_rect = QRect(...)
            
            if eraser_rect.intersects(scaled_rect):
                to_remove.append(i)
        
        # Remove highlighter paths from back to front
        for i in sorted(to_remove, reverse=True):
            del self.highlighter_paths[i]

    def activate(self):
        """Activate drawing mode"""

    def reset_state(self):
        """Reset state variables to initial values"""

    def cleanup_resources(self):
        """Clean up resources"""

    def wheelEvent(self, event):
        """Mouse wheel event handler - Zoom in/out functionality"""

    def mousePressEvent(self, event):
        """Mouse click event handler"""

    def focusOutEvent(self, event):
        """Focus loss event handler"""

    def closeEvent(self, event):
        """Window close event handler"""

    # 포커스 상실 시 자동으로 다시 포커스 획득 시도
    # Automatically attempt to regain focus when focus is lost