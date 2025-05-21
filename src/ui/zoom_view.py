from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QTimer, pyqtSignal, QSize, QSettings
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QScreen, QCursor, QTransform, QPainterPath
import logging

logger = logging.getLogger(__name__)

class ZoomView(QWidget):
    closed = pyqtSignal()  # Signal emitted when zoom view is closed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Basic settings
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Screen size settings
        self.screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(self.screen_geometry)

        # ▶ Initialize QPainterPath for highlighter path storage
        self.highlight_path = QPainterPath()
        
        # State variables
        self.scale_factor = 1.0  # Initial zoom ratio (1.0 = original size)
        self.scale_factor_min = 1.0  # Minimum zoom ratio (original size)
        self.scale_factor_max = 5.0  # Maximum zoom ratio
        self.scale_step = 0.2  # Zoom step size
        self.zoom_center = None  # Zoom center point
        self.drawing_mode = False  # Whether drawing mode is active
        self.last_pos = None  # Last mouse position
        self.screen_capture = None  # Screen capture image
        self.original_screen_capture = None  # Original screen capture image (no transformation)
        
        # Drawing-related variables
        self.drawings = []  # List to store drawn lines [(start_point, end_point), ...]
        settings = QSettings()
        self.pen_color = settings.value("pen/color1", QColor(255, 0, 0), type=QColor)  # Default pen color (red)
        self.pen_width = settings.value("pen/width", 3, int)  # Default pen thickness
        
        # Panning-related variables
        self.panning = False  # Panning mode state
        self.pan_start_pos = None  # Panning start position
        self.pan_offset = QPoint(0, 0)  # Panning offset
        
        # Circular cursor-related variables
        self.circle_cursor_size = 50
        self.circle_cursor_min_size = 0  # Minimum size
        self.circle_cursor_max_size = 100  # Maximum size
        self.circle_cursor_step = 5  # Circular cursor size adjustment step
        self.circle_cursor_opacity = 0.2  # Opacity (0.2 = 80% transparent)
        self.circle_cursor_color = settings.value("cursor/color", QColor(0, 120, 215), type=QColor)  # Blue color, opacity applied
        self.circle_cursor_color.setAlpha(int(255 * self.circle_cursor_opacity))
        self.current_cursor_pos = QPoint(0, 0)  # Current cursor position
        self.circle_cursor_was_visible = True  # Whether circular cursor was originally visible
        
        # Cursor image-related variables
        self.pencil_cursor = None  # Pencil cursor image
        
        # MainWindow's circular cursor reference (for hiding during capture)
        self.main_window_circle_cursor = None
        
        # Setup for tracking mouse movement events
        self.setMouseTracking(True)

       # ▶ 투명도를 낮추고 두께를 2배로 늘림
        alpha = settings.value("highlight/opacity", 64, int)
        hl_color = settings.value("highlight/color1", QColor(255, 255, 0), type=QColor)  # 기본은 노란색
        hl_color.setAlpha(alpha)
        self.highlighter_color = hl_color
        self.highlighter_width = settings.value("highlight/width", 20, int)
        # ▶ 끝처리, 교차부 스타일 지정 (겹쳐도 원형 엔드캡 없음)
        self.highlighter_cap   = Qt.PenCapStyle.FlatCap     # FlatCap: Remove circular end part
        self.highlighter_join  = Qt.PenJoinStyle.MiterJoin  # MiterJoin: Connect sharply
        # ▶ 현재 드로잉 색상·두께 초기값 (pen_color/pen_width 사용)
        self.current_color = self.pen_color
        self.current_width = self.pen_width
        
        # 현재 활성 도구 추적 변수 추가
        self.highlighter_active = False

        # ── Eraser 설정 ──
        self.eraser_size = 20  # Default eraser size (20x20 pixels)
        self.eraser_min_size = 5  # Minimum eraser size
        self.eraser_max_size = 100  # Maximum eraser size
        self.eraser_step = 5  # Size adjustment step
        self.eraser_color = QColor(255, 0, 0, 128)  # Semi-transparent red color for eraser
        self.eraser_active = False  # Whether eraser is currently active
        
        # 저장된 하이라이트 경로를 관리하는 배열 추가
        self.highlighter_paths = []
        
        # 스레드 관련 변수 추가
        self._cleanup_required = False
        
        logger.debug("ZoomView initialized")

    def erase_at_position(self, pos):
        """Erase drawing at specified position"""
        # 화면 좌표를 이미지 좌표로 변환
        image_pos = self.screen_to_image(pos)
        
        # 현재 확대/축소 비율을 고려한 지우개 크기 계산
        scaled_eraser_size = self.eraser_size / self.scale_factor
        
        # 지우개 영역 계산 (이미지 좌표계에서)
        eraser_rect = QRect(
            int(image_pos.x() - scaled_eraser_size / 2),
            int(image_pos.y() - scaled_eraser_size / 2),
            int(scaled_eraser_size),
            int(scaled_eraser_size)
        )
        
        # 지울 그림 찾기
        to_remove = []
        for i, (start_pt, end_pt, col, wd) in enumerate(self.drawings):
            # 선분의 경계 상자 계산 (이미지 좌표계에서)
            line_rect = QRect(
                int(min(start_pt.x(), end_pt.x()) - wd/2),
                int(min(start_pt.y(), end_pt.y()) - wd/2),
                int(abs(end_pt.x() - start_pt.x()) + wd),
                int(abs(end_pt.y() - start_pt.y()) + wd)
            )
            
            # 지우개 영역과 선분이 겹치면 제거 목록에 추가
            if eraser_rect.intersects(line_rect):
                to_remove.append(i)
        
        # 뒤에서부터 제거 (인덱스 변화 방지)
        for i in sorted(to_remove, reverse=True):
            del self.drawings[i]
        
        # 하이라이터 경로도 확인하고 제거
        to_remove = []
        for i, path_info in enumerate(self.highlighter_paths):
            # 하이라이터 경로의 경계 상자를 이미지 좌표계로 변환
            path_rect = path_info['path'].boundingRect()
            scaled_rect = QRect(
                int(path_rect.x() - path_info['width']/2),
                int(path_rect.y() - path_info['width']/2),
                int(path_rect.width() + path_info['width']),
                int(path_rect.height() + path_info['width'])
            )
            
            if eraser_rect.intersects(scaled_rect):
                to_remove.append(i)
        
        # 하이라이터 경로도 뒤에서부터 제거
        for i in sorted(to_remove, reverse=True):
            del self.highlighter_paths[i]

    def _init_pencil_cursor(self):
        """Initialize pencil cursor shape"""
        try:
            # Try to load pencil cursor image (from resources folder)
            pencil_pixmap = QPixmap("resources/pencil_cursor.png")
            if pencil_pixmap.isNull():
                # If not found, use built-in pencil cursor
                self.pencil_cursor = Qt.CursorShape.CrossCursor
                logger.debug("Using built-in cross cursor as pencil cursor")
            else:
                # Set hotspot position to pencil tip (5, 5)
                self.pencil_cursor = QCursor(pencil_pixmap, 1, 1)
                logger.debug("Custom pencil cursor loaded with hotspot at pencil tip (5, 5)")
        except Exception as e:
            # If error occurs, use default pencil cursor
            self.pencil_cursor = Qt.CursorShape.CrossCursor
            logger.error(f"Failed to load pencil cursor: {e}")
    
    def activate(self):
        """Activate drawing mode"""
        try:
            # 이전 세션의 정리가 필요한 경우 정리 수행
            if self._cleanup_required:
                self.cleanup_resources()
            
            # 초기 상태 재설정
            self.reset_state()
            
            # 펜슬 커서 초기화
            self._init_pencil_cursor()
            
            # circular cursor 상태 저장
            if self.main_window_circle_cursor:
                was_visible = self.main_window_circle_cursor.isVisible()
                self.circle_cursor_was_visible = was_visible
                logger.debug(f"Saved initial circle cursor visibility state: {was_visible}")
            
            # 성능 개선: 화면 표시 먼저 하고 캡처는 나중에
            # 윈도우 표시 및 포커스 설정
            self.show()
            self.raise_()
            self.activateWindow()
            self.setFocus()
            
            # 포커스 정책 설정
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
            # 펜슬 커서로 변경
            if self.pencil_cursor:
                self.setCursor(self.pencil_cursor)
            
            # 화면 캡처 - 원형 커서가 보이지 않도록 처리됨
            self.capture_screen()
            
            self._cleanup_required = True
            
            logger.debug("ZoomView UI initialized, screen capture completed")
        except Exception as e:
            logger.error(f"Error during ZoomView activation: {e}")
            self.close_zoom_view()
            raise

    def _delayed_capture_and_setup(self):
        """스레드 충돌 없이 캡처 작업 수행"""
        try:
            # 화면 캡처 수행
            capture_success = self.capture_screen()
            if not capture_success:
                logger.error("Screen capture failed, closing zoom view")
                self.close_zoom_view()
                return
            
            # 현재 마우스 위치를 줌 중심으로 설정
            self.zoom_center = QCursor.pos()
            self.current_cursor_pos = self.zoom_center
            
            # 그리기 모드 활성화
            self.drawing_mode = True
            
            self._cleanup_required = True
            
            # 화면 업데이트
            self.update()
            
            logger.debug(f"ZoomView delayed setup completed at {self.zoom_center}")
            logger.debug(f"Drawing mode enabled")
        except Exception as e:
            logger.error(f"Error during delayed setup: {e}")
            self.close_zoom_view()

    def reset_state(self):
        """Reset state variables to initial state"""
        self.scale_factor = 1.0
        self.zoom_center = None
        self.last_pos = None
        self.drawing_mode = False
        self.panning = False
        self.pan_start_pos = None
        self.pan_offset = QPoint(0, 0)
        self.highlight_path = QPainterPath()
        self.drawings = []
        self.highlighter_paths = []
        self.eraser_active = False
        self.highlighter_active = False

    def cleanup_resources(self):
        """Clean up resources"""
        try:
            # 스크린 캡처 이미지 정리
            if self.screen_capture:
                self.screen_capture = None
            if self.original_screen_capture:
                self.original_screen_capture = None
            
            # 펜슬 커서 정리
            if self.pencil_cursor:
                self.pencil_cursor = None
            
            # 스레드 관련 데이터 정리
            self.drawings = []
            self.highlighter_paths = []
            
            # 모든 이벤트 처리 완료
            QApplication.processEvents()
            
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")

    def capture_screen(self):
        """Capture current screen"""
        try:
            logger.debug("Starting screen capture...")
            
            # 캡처 전에 원형 커서 숨기기 - ZoomView와 MainWindow의 두 커서 모두 숨김
            main_cursor_visible = False
            if self.main_window_circle_cursor and self.main_window_circle_cursor.isVisible():
                main_cursor_visible = True
                self.main_window_circle_cursor.hide()
                # 화면 갱신을 위해 잠시 대기
                QApplication.processEvents()
            
            # 화면 캡처 지연 - 커서가 완전히 사라질 시간을 줌
            QTimer.singleShot(50, lambda: self._complete_capture(main_cursor_visible))
            
            return True
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return False

    def _complete_capture(self, main_cursor_visible):
        """커서가 화면에서 사라진 후 실제 캡처 수행"""
        try:
            # 오래 걸리는 화면 캡처 작업 최적화
            pixmap = QApplication.primaryScreen().grabWindow(0)
            self.original_screen_capture = pixmap
            self.screen_capture = pixmap
            
            # 캡처 완료 후 필요한 경우 원형 커서 다시 표시
            if main_cursor_visible and self.main_window_circle_cursor:
                # 메인 화면에서의 원형 커서는 다시 표시하지 않음 (ZoomView 내에서는 다른 커서 사용)
                pass
            
            # 화면 업데이트
            self.update()
            
            # 현재 마우스 위치를 줌 중심으로 설정
            self.zoom_center = QCursor.pos()
            self.current_cursor_pos = self.zoom_center
            
            # 그리기 모드 활성화
            self.drawing_mode = True
            
            logger.debug(f"Screen capture completed: {pixmap.width()}x{pixmap.height()}")
        except Exception as e:
            logger.error(f"Delayed screen capture failed: {e}")

    def get_transform(self):
        """Return transformation matrix suitable for current zoom/shrink/pan state"""
        transform = QTransform()
        
        # Apply pan offset
        transform.translate(self.pan_offset.x(), self.pan_offset.y())
        
        # Apply zoom/shrink (zoom_center as reference)
        transform.translate(self.zoom_center.x(), self.zoom_center.y())
        transform.scale(self.scale_factor, self.scale_factor)
        transform.translate(-self.zoom_center.x(), -self.zoom_center.y())
        
        return transform
    
    def get_inverse_transform(self):
        """Return inverse transformation matrix"""
        # Calculate inverse matrix of current transformation matrix
        return self.get_transform().inverted()[0]
    
    def paintEvent(self, event):
        """Screen drawing event"""
        # 화면 캡처가 없으면 아무것도 그리지 않음
        if not self.original_screen_capture:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 성능 개선: 클리핑 영역 설정으로 불필요한 그리기 방지
        painter.setClipRect(event.rect())
        
        # 원본 크기(1.0)이고 패닝이 없는 경우
        if self.scale_factor == 1.0 and self.pan_offset == QPoint(0, 0):
            # 화면 전체에 캡처된 이미지 표시
            painter.drawPixmap(self.rect(), self.original_screen_capture)
        
            # ● 드로잉 (색상·두께 반영)
            # 성능 개선: 배치 처리로 그리기 작업 최적화
            batch_size = 20
            for i in range(0, len(self.drawings), batch_size):
                batch = self.drawings[i:i+batch_size]
                for start_pt, end_pt, col, wd in batch:
                    pen = QPen(col, wd)
                    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    painter.setPen(pen)
                    painter.drawLine(start_pt, end_pt)
            
            # ● 저장된 하이라이트 경로 모두 그리기
            highlight_pen = QPen()
            highlight_pen.setCapStyle(self.highlighter_cap)
            highlight_pen.setJoinStyle(self.highlighter_join)
            
            # 성능 개선: 같은 색상/두께 경로는 한 번에 그리기
            current_color = None
            current_width = None
            
            for path_info in self.highlighter_paths:
                if current_color != path_info['color'] or current_width != path_info['width']:
                    current_color = path_info['color']
                    current_width = path_info['width']
                    highlight_pen.setColor(current_color)
                    highlight_pen.setWidth(current_width)
                    painter.setPen(highlight_pen)
                painter.drawPath(path_info['path'])
            
            # ● 현재 그리는 중인 하이라이터 경로 그리기
            if not self.highlight_path.isEmpty():
                highlight_pen = QPen(self.highlighter_color, self.highlighter_width)
                highlight_pen.setCapStyle(self.highlighter_cap)
                highlight_pen.setJoinStyle(self.highlighter_join)
                painter.setPen(highlight_pen)
                painter.drawPath(self.highlight_path)
        
        # 확대된 경우 (scale_factor > 1.0) 또는 패닝된 경우
        else:
            # 변환 행렬 적용
            painter.setTransform(self.get_transform())
            painter.drawPixmap(0, 0, self.original_screen_capture)
            
            # ● 드로잉 (색상·두께 반영)
            for start_pt, end_pt, col, wd in self.drawings:
                pen = QPen(col, wd)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawLine(start_pt, end_pt)
            
            # ● 저장된 하이라이트 경로 모두 그리기
            for path_info in self.highlighter_paths:
                highlight_pen = QPen(path_info['color'], path_info['width'])
                highlight_pen.setCapStyle(self.highlighter_cap)
                highlight_pen.setJoinStyle(self.highlighter_join)
                painter.setPen(highlight_pen)
                painter.drawPath(path_info['path'])
            
            # ● 현재 그리는 중인 하이라이터 경로 그리기
            highlight_pen = QPen(self.highlighter_color, self.highlighter_width)
            highlight_pen.setCapStyle(self.highlighter_cap)
            highlight_pen.setJoinStyle(self.highlighter_join)
            painter.setPen(highlight_pen)
            painter.drawPath(self.highlight_path)
        
        # Reset transformation (UI elements drawn on original coordinates)
        painter.resetTransform()
        
        # Draw circular cursor (based on mouse position)
        if self.circle_cursor_size > 0:
            painter.setPen(Qt.PenStyle.NoPen)  # No outline
            painter.setBrush(self.circle_cursor_color)  # Circle color and opacity
            
            # Set circle center to current mouse position
            circle_rect = QRect(
                self.current_cursor_pos.x() - self.circle_cursor_size // 2,
                self.current_cursor_pos.y() - self.circle_cursor_size // 2,
                self.circle_cursor_size,
                self.circle_cursor_size
            )
            painter.drawEllipse(circle_rect)
        
        # Display current zoom/shrink ratio (only when not 1.0)
        if self.scale_factor != 1.0:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(10, 30, f"Zoom ratio: {self.scale_factor:.1f}x")
            
        # Display circular cursor size (only when not 0)
        if self.circle_cursor_size > 0:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(10, 50, f"Cursor size: {self.circle_cursor_size}px")

        # Draw eraser cursor when active
        if self.eraser_active:
            painter.resetTransform()  # 화면 좌표계로 리셋
            
            # 반투명한 빨간색 사각형으로 지우개 표시
            painter.setPen(QPen(QColor(0, 0, 0, 180), 1))  # 검은색 테두리
            painter.setBrush(QColor(255, 0, 0, 60))  # 반투명한 빨간색
            
            # 현재 마우스 위치에 지우개 사각형 그리기
            screen_pos = self.current_cursor_pos
            eraser_rect = QRect(
                screen_pos.x() - self.eraser_size // 2,
                screen_pos.y() - self.eraser_size // 2,
                self.eraser_size,
                self.eraser_size
            )
            painter.drawRect(eraser_rect)
            
            # 지우개 크기 표시
            if self.eraser_active and (QApplication.mouseButtons() & Qt.MouseButton.LeftButton) and (QApplication.mouseButtons() & Qt.MouseButton.RightButton):
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(10, 70, f"Eraser size: {self.eraser_size}px")

    def wheelEvent(self, event):
        """마우스 휠 이벤트 처리 - 확대/축소 기능"""
        if not self.drawing_mode:
            # 그리기 모드가 아니면 무시
            return
        
        # 휠 방향에 따라 확대/축소 비율 조정
        delta = event.angleDelta().y()
        
        # 현재 마우스 위치 저장 (화면 좌표)
        mouse_pos = event.position().toPoint()
        
        # 현재 마우스 위치를 이미지 좌표계로 변환
        old_pos = self.screen_to_image(mouse_pos)
        
        old_scale = self.scale_factor
        
        # 휠 위로: 확대
        if delta > 0:
            self.scale_factor = min(self.scale_factor_max, self.scale_factor + self.scale_step)
            logger.debug(f"Zoom in: scale factor = {self.scale_factor:.1f}x")
            
            # 확대 시에는 마우스 포인터를 중심으로
            self.zoom_center = mouse_pos
            
            # 마우스 위치가 동일한 이미지 지점을 가리키도록 패닝 오프셋 조정
            new_pos = self.image_to_screen(old_pos)
            self.pan_offset += mouse_pos - new_pos
            
        # 휠 아래로: 축소
        else:
            new_scale = max(self.scale_factor_min, self.scale_factor - self.scale_step)
            scale_changed = new_scale != self.scale_factor
            
            if scale_changed:
                # 화면 중앙점 계산
                screen_center = QPoint(self.width() // 2, self.height() // 2)
                
                # 현재 변환 상태에서 화면 중앙이 가리키는 이미지 좌표
                current_center = self.screen_to_image(screen_center)
                
                # 축소 비율에 따른 중앙 이동 비율 계산
                # scale_factor가 1.0에 가까워질수록 transition_factor가 1.0에 가까워짐
                scale_range = self.scale_factor_max - self.scale_factor_min
                current_scale_position = (self.scale_factor - self.scale_factor_min) / scale_range
                transition_factor = 1.0 - current_scale_position
                
                # 현재 줌 중심점과 화면 중앙점 사이의 보간
                if self.zoom_center is not None:
                    new_center = QPoint(
                        int(self.zoom_center.x() * (1 - transition_factor) + screen_center.x() * transition_factor),
                        int(self.zoom_center.y() * (1 - transition_factor) + screen_center.y() * transition_factor)
                    )
                    self.zoom_center = new_center
                else:
                    self.zoom_center = screen_center
                
                # 새로운 스케일 적용
                self.scale_factor = new_scale
                logger.debug(f"Zoom out: scale factor = {self.scale_factor:.1f}x")
                
                # 새로운 변환 상태에서 화면 중앙이 가리키는 이미지 좌표
                new_center = self.screen_to_image(self.zoom_center)
                
                # 패닝 오프셋 조정
                screen_new_center = self.image_to_screen(current_center)
                self.pan_offset += self.zoom_center - screen_new_center
                
                # 이미지가 화면을 벗어나지 않도록 패닝 오프셋 제한
                self.adjust_pan_offset()
        
        # 화면 업데이트
        self.update()
        
        # 포커스 및 활성 상태 유지
        self.setFocus()
        self.activateWindow()
        
        # 이벤트 수락
        event.accept()

    def adjust_pan_offset(self):
        """이미지가 화면을 벗어나지 않도록 패닝 오프셋을 조정"""
        if self.scale_factor <= 1.0:
            # 축소 상태에서는 이미지를 화면 중앙에 위치시킴
            screen_center = QPoint(self.width() // 2, self.height() // 2)
            image_center = QPoint(
                int(self.original_screen_capture.width() * self.scale_factor / 2),
                int(self.original_screen_capture.height() * self.scale_factor / 2)
            )
            self.pan_offset = screen_center - image_center
            return
        
        # 이미지 크기 계산
        scaled_width = int(self.original_screen_capture.width() * self.scale_factor)
        scaled_height = int(self.original_screen_capture.height() * self.scale_factor)
        
        # 최대 허용 오프셋 계산
        max_x_offset = max(0, (scaled_width - self.width()) // 2)
        max_y_offset = max(0, (scaled_height - self.height()) // 2)
        
        # X축 오프셋 제한
        if self.pan_offset.x() > max_x_offset:
            self.pan_offset.setX(max_x_offset)
        elif self.pan_offset.x() < -max_x_offset:
            self.pan_offset.setX(-max_x_offset)
        
        # Y축 오프셋 제한
        if self.pan_offset.y() > max_y_offset:
            self.pan_offset.setY(max_y_offset)
        elif self.pan_offset.y() < -max_y_offset:
            self.pan_offset.setY(-max_y_offset)

    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        # 포커스 확보
        self.setFocus()
        self.activateWindow()
        
        # 기존 마우스 이벤트 처리
        modifiers = QApplication.keyboardModifiers()
        
        # Hold Shift key and click left mouse button: Enable panning mode
        if modifiers == Qt.KeyboardModifier.ShiftModifier and event.button() == Qt.MouseButton.LeftButton:
            self.panning = True
            self.pan_start_pos = event.position().toPoint()
            logger.debug(f"Panning started at {self.pan_start_pos}")
            return
            
        if self.drawing_mode:
            # Record start point (convert to image coordinate system)
            self.last_pos = self.screen_to_image(event.position().toPoint())
            
            # Check if both left and right buttons are pressed (eraser mode)
            buttons = QApplication.mouseButtons()
            if buttons & Qt.MouseButton.LeftButton and buttons & Qt.MouseButton.RightButton:
                self.eraser_active = True
                logger.debug(f"Eraser activated at {self.last_pos} with size {self.eraser_size}px")
                self.erase_at_position(self.last_pos)
                self.update()
                return

            # ── Right-click: Start highlighter mode ──
            if event.button() == Qt.MouseButton.RightButton:
                # 현재 설정된 하이라이트 색상과 두께를 사용
                self.current_color = self.highlighter_color
                self.current_width = self.highlighter_width
                self.highlighter_active = True  # 하이라이터 활성화 상태 기록
                # Set start position for Path
                p = self.last_pos
                self.highlight_path = QPainterPath()  # 새로운 경로 시작 (기존 경로는 이미 self.drawings에 저장됨)
                self.highlight_path.moveTo(QPointF(p.x(), p.y()))
                logger.debug(f"Highlight started at {p}")
                return

            # ── Left-click: Start basic pen mode ──
            if event.button() == Qt.MouseButton.LeftButton:
                self.current_color = self.pen_color
                self.current_width = self.pen_width
                self.highlighter_active = False  # 펜 활성화 상태 기록
                logger.debug(f"Pen drawing started at {self.last_pos}")
                return

    
    def mouseMoveEvent(self, event):
        """Mouse movement event"""
        # Update current mouse position (for circular cursor)
        self.current_cursor_pos = event.position().toPoint()
        
        # When dragging in pan mode
        if self.panning and self.pan_start_pos:
            current_pos = event.position().toPoint()
            delta = current_pos - self.pan_start_pos
            
            # 패닝 오프셋 업데이트
            self.pan_offset += delta
            self.pan_start_pos = current_pos
            
            logger.debug(f"Panning: offset = {self.pan_offset}")
            self.update()
            return
            
        # When dragging in drawing mode
        if self.drawing_mode:
            # Check if both buttons are still pressed for eraser
            buttons = QApplication.mouseButtons()
            if buttons & Qt.MouseButton.LeftButton and buttons & Qt.MouseButton.RightButton:
                if not self.eraser_active:
                    self.eraser_active = True
                self.erase_at_position(self.current_cursor_pos)
                self.update()
                return

            # If not both buttons pressed, deactivate eraser
            self.eraser_active = False
            
            # ▶ Right-click drag: Extend highlighter path
            if event.buttons() & Qt.MouseButton.RightButton:
                pt = self.screen_to_image(event.position().toPoint())
                self.highlight_path.lineTo(QPointF(pt.x(), pt.y()))
                self.update()
                return

            # ▶ Left-click drag: Draw pen line
            if self.last_pos and (event.buttons() & Qt.MouseButton.LeftButton):
                current_pos = self.screen_to_image(event.position().toPoint())
                # Include color(self.current_color) and thickness(self.current_width) information
                self.drawings.append((
                    self.last_pos,
                    current_pos,
                    self.current_color,
                    self.current_width
                ))
                self.last_pos = current_pos
                
                logger.debug(f"Drawing line from {self.drawings[-1][0]} to {self.drawings[-1][1]}")
                self.update()
                return

        # Otherwise: Simple update (circular cursor, etc.)
        self.update()

    
    def mouseReleaseEvent(self, event):
        """Mouse release event"""
        # End pan mode
        if self.panning and event.button() == Qt.MouseButton.LeftButton:
            self.panning = False
            self.pan_start_pos = None
            logger.debug("Panning ended")
            return
            
        # Check if eraser should be deactivated
        buttons = QApplication.mouseButtons()
        if not (buttons & Qt.MouseButton.LeftButton and buttons & Qt.MouseButton.RightButton):
            self.eraser_active = False
            logger.debug("Eraser deactivated")
        
        # Add highlighter path to array when path is completed
        if self.drawing_mode and event.button() == Qt.MouseButton.RightButton and not self.highlight_path.isEmpty():
            # 현재 경로를 복제하여 저장 (색상, 두께 정보 포함)
            current_path = {
                'path': QPainterPath(self.highlight_path),  # 경로 복제
                'color': QColor(self.highlighter_color),    # 색상 복제
                'width': self.highlighter_width             # 두께 저장
            }
            self.highlighter_paths.append(current_path)
            logger.debug(f"Highlight path added to collection, total: {len(self.highlighter_paths)}")
            
            # Reset current path (for new drawing)
            self.highlight_path = QPainterPath()
        
        if self.drawing_mode:
            self.last_pos = None

    def keyPressEvent(self, event):
        """Handle keyboard events"""
        key = event.key()
        
        # ESC 키 처리를 최우선으로 수행
        if key == Qt.Key.Key_Escape:
            logger.debug("ESC key pressed - closing zoom view")
            # 포커스 확인 로깅 추가
            logger.debug(f"Widget has focus: {self.hasFocus()}")
            logger.debug(f"Widget is active window: {self.isActiveWindow()}")
            self.close_zoom_view()
            event.accept()  # 이벤트 처리 완료 표시
            return
        
        # 나머지 키 이벤트 처리
        modifiers = QApplication.keyboardModifiers()
        buttons = QApplication.mouseButtons()
        
        # 지우개 모드에서 +/- 키로 크기 조절
        if self.eraser_active and (buttons & Qt.MouseButton.LeftButton) and (buttons & Qt.MouseButton.RightButton):
            if key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
                old_size = self.eraser_size
                self.eraser_size = min(self.eraser_max_size, self.eraser_size + self.eraser_step)
                logger.debug(f"Eraser size increased from {old_size} to {self.eraser_size}px")
                self.update()
                return
            elif key == Qt.Key.Key_Minus:
                old_size = self.eraser_size
                self.eraser_size = max(self.eraser_min_size, self.eraser_size - self.eraser_step)
                logger.debug(f"Eraser size decreased from {old_size} to {self.eraser_size}px")
                self.update()
                return
        
        # 설정에서 색상 값 불러오기 함수
        settings = QSettings()
        
        # 1/2/3: Pen color 변경
        if key == Qt.Key.Key_1:
            self.pen_color = settings.value("pen/color1", QColor(255, 0, 0), type=QColor)
            logger.debug(f"Pen color changed to custom color 1: {self.pen_color.name()}")
            return
        elif key == Qt.Key.Key_2:
            self.pen_color = settings.value("pen/color2", QColor(0, 255, 0), type=QColor)
            logger.debug(f"Pen color changed to custom color 2: {self.pen_color.name()}")
            return
        elif key == Qt.Key.Key_3:
            self.pen_color = settings.value("pen/color3", QColor(0, 0, 255), type=QColor)
            logger.debug(f"Pen color changed to custom color 3: {self.pen_color.name()}")
            return

        # 4/5/6: Highlight color 변경 (설정값 사용)
        elif key == Qt.Key.Key_4:
            alpha = self.highlighter_color.alpha()  # 현재 투명도 유지
            self.highlighter_color = settings.value("highlight/color1", QColor(255, 255, 0, alpha), type=QColor)
            logger.debug(f"Highlight color changed to custom highlight 1: {self.highlighter_color.name()}")
            return
        elif key == Qt.Key.Key_5:
            alpha = self.highlighter_color.alpha()
            self.highlighter_color = settings.value("highlight/color2", QColor(144, 238, 144, alpha), type=QColor)
            logger.debug(f"Highlight color changed to custom highlight 2: {self.highlighter_color.name()}")
            return
        elif key == Qt.Key.Key_6:
            alpha = self.highlighter_color.alpha()
            self.highlighter_color = settings.value("highlight/color3", QColor(255, 105, 180, alpha), type=QColor)
            logger.debug(f"Highlight color changed to custom highlight 3: {self.highlighter_color.name()}")
            return

        # + / = : Eraser size 조절, Zoom or Pen/Highlight thickness 조절
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                # Ctrl++: Increase zoom ratio
                old_factor = self.scale_factor
                self.scale_factor = min(self.scale_factor_max, self.scale_factor + self.scale_step)
                logger.debug(f"Zoom factor increased to {self.scale_factor:.1f}x")
                # 화면 중심을 기준으로 줌
                center = QPoint(self.width() // 2, self.height() // 2)
                self.zoom_center = center
                self.update()
                return
            else:
                # + 키만 누를 경우: 현재 활성 도구의 크기 증가
                if self.eraser_active:
                    old_size = self.eraser_size
                    self.eraser_size = min(self.eraser_max_size, self.eraser_size + 5)
                    logger.debug(f"Eraser size increased from {old_size} to {self.eraser_size}px")
                elif hasattr(self, 'highlighter_active') and self.highlighter_active:
                    old_width = self.highlighter_width
                    self.highlighter_width = min(50, self.highlighter_width + 2)
                    logger.debug(f"Highlight width increased to {self.highlighter_width}px")
                else:
                    old_width = self.pen_width
                    self.pen_width = min(20, self.pen_width + 1)
                    logger.debug(f"Pen width increased to {self.pen_width}px")
                self.update()
            return

        # - : Eraser size 조절, Zoom out or Pen/Highlight thickness 감소
        elif key == Qt.Key.Key_Minus:
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                # Ctrl+-: Decrease zoom ratio
                old_factor = self.scale_factor
                self.scale_factor = max(self.scale_factor_min, self.scale_factor - self.scale_step)
                logger.debug(f"Zoom factor decreased to {self.scale_factor:.1f}x")
                center = QPoint(self.width() // 2, self.height() // 2)
                self.zoom_center = center
                self.update()
                return
            else:
                # - 키만 누를 경우: 현재 활성 도구의 크기 감소
                if self.eraser_active:
                    old_size = self.eraser_size
                    self.eraser_size = max(self.eraser_min_size, self.eraser_size - 5)
                    logger.debug(f"Eraser size decreased from {old_size} to {self.eraser_size}px")
                elif hasattr(self, 'highlighter_active') and self.highlighter_active:
                    old_width = self.highlighter_width
                    self.highlighter_width = max(5, self.highlighter_width - 2)
                    logger.debug(f"Highlight width decreased to {self.highlighter_width}px")
                else:
                    old_width = self.pen_width
                    self.pen_width = max(1, self.pen_width - 1)
                    logger.debug(f"Pen width decreased to {self.pen_width}px")
                self.update()
            return

        # R: Reset view (panning offset 및 zoom factor 초기화)
        elif key == Qt.Key.Key_R:
            self.pan_offset = QPoint(0, 0)
            self.scale_factor = 1.0
            logger.debug("Reset view: panning offset and scale factor reset")
            self.update()
            return

        # 그 외: 기본 처리
        super().keyPressEvent(event)

    
    def close_zoom_view(self):
        """End drawing mode"""
        try:
            # 그리기 모드 비활성화
            self.drawing_mode = False
            
            # 원래의 circular cursor 상태 복원
            if self.main_window_circle_cursor:
                if self.circle_cursor_was_visible:
                    if self.circle_cursor_size > 0:
                        self.main_window_circle_cursor.size = self.circle_cursor_size
                        self.main_window_circle_cursor.color = self.circle_cursor_color
                        self.main_window_circle_cursor.show()
                        logger.debug(f"Restored main window circle cursor (size={self.circle_cursor_size})")
                        QApplication.processEvents()
            
            # 리소스 정리
            self.cleanup_resources()
            
            # 닫기 신호 발생 및 창 닫기
            logger.debug("Closing zoom view...")
            self.closed.emit()
            self.close()
            
            self._cleanup_required = False
            logger.debug("Zoom view closed successfully")
            
        except Exception as e:
            logger.error(f"Error during zoom view closure: {e}")
            # 강제로 창 닫기 시도
            self.close()

    def screen_to_image(self, screen_point):
        """Convert screen coordinates to image coordinates"""
        # Apply inverse transformation to screen coordinates -> image coordinates
        return self.get_inverse_transform().map(screen_point)
    
    def image_to_screen(self, image_point):
        """Convert image coordinates to screen coordinates"""
        # Apply current transformation matrix to image coordinates -> screen coordinates
        return self.get_transform().map(image_point)

    def focusOutEvent(self, event):
        """Handle focus loss event"""
        super().focusOutEvent(event)
        logger.debug("Focus lost - attempting to restore focus")
        # 포커스 상실 시 자동으로 다시 포커스 획득 시도
        self.setFocus()
        self.activateWindow() 

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # 정상적인 종료인 경우
            if QApplication.instance().isSavingSession() or QApplication.instance().aboutToQuit.isConnected():
                self.cleanup_resources()
                # 스레드 관련 변수 초기화
                self._cleanup_required = False
                event.accept()
            else:
                # 리소스 정리
                self.cleanup_resources()
                # 스레드 관련 변수 초기화
                self._cleanup_required = False
                # 창 숨기기만 하고 이벤트 무시
                self.hide()
                event.ignore()
        except Exception as e:
            logger.error(f"Error in closeEvent: {e}")
            # 스레드 관련 변수 초기화
            self._cleanup_required = False
            event.accept() 