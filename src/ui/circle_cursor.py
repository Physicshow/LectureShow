from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor
import logging

logger = logging.getLogger(__name__)

class CircleCursor(QWidget):
    """
    원형 커서 위젯 - 마우스 포인터를 따라다니는 반투명 원형 커서
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 기본 설정
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # 마우스 이벤트를 통과시킴
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput  # 마우스 입력 투명 처리
        )
        
        # 포커스 비활성화 (별도 설정)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # 원형 커서 관련 변수
        self._size = 50  # 원형 커서 크기 (지름, 픽셀 단위)
        self._min_size = 0  # 최소 크기
        self._max_size = 160  # 최대 크기
        self._step = 5  # 크기 조절 단계
        self._opacity = 0.2  # 불투명도 (0.2 = 80% 투명)
        self._color = QColor(255, 20, 147, int(255 * self._opacity))  # 분홍색, 투명도 적용
        
        # 위젯 크기 설정 (충분히 크게 설정하여 전체 화면 커버)
        desktop = self.screen().size()
        self.setGeometry(0, 0, desktop.width(), desktop.height())
        
        # 마우스 트래킹 활성화
        self.setMouseTracking(True)
        
        self.show()
        logger.debug("CircleCursor initialized with click pass-through")
    
    @property
    def size(self):
        return self._size
        
    @size.setter
    def size(self, value):
        """원형 커서 크기 설정"""
        self._size = max(self._min_size, min(self._max_size, value))
        self.update()
        
    @property
    def color(self):
        return self._color
        
    @color.setter
    def color(self, value):
        """원형 커서 색상 설정"""
        if isinstance(value, QColor):
            # 원본 색상의 RGB 값만 사용하고 기존 알파값 유지
            new_color = QColor(value.red(), value.green(), value.blue(), int(255 * self._opacity))
            self._color = new_color
        else:
            # 기본값 - 파란색, 기존 불투명도 적용
            self._color = QColor(0, 120, 215, int(255 * self._opacity))
        
        # 즉시 화면 갱신
        self.update()
    
    def paintEvent(self, event):
        """화면 그리기 이벤트"""
        if self._size <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 원형 커서 그리기
        painter.setPen(Qt.PenStyle.NoPen)  # 테두리 없음
        painter.setBrush(self._color)  # 원 색상 및 투명도
        
        # 마우스 위치를 기준으로 원 그리기
        pos = self.mapFromGlobal(self.cursor().pos())
        circle_rect = QRect(
            pos.x() - self._size // 2,
            pos.y() - self._size // 2,
            self._size,
            self._size
        )
        painter.drawEllipse(circle_rect)
    
    def update_position(self, pos=None):
        """마우스 위치에 따라 원형 커서 업데이트"""
        # 항상 업데이트하여 마우스를 쫓아다니게 함
        self.update()
        # 로그 비활성화 (너무 많은 로그 출력 방지)
        # logger.debug(f"Circle cursor position updated: {self.cursor().pos()}")
    
    def increase_size(self):
        """원형 커서 크기 증가"""
        old_size = self._size
        self._size = min(self._max_size, self._size + self._step)
        if old_size != self._size:
            logger.debug(f"Circle cursor size increased to {self._size}px")
            self.update()
    
    def decrease_size(self):
        """원형 커서 크기 감소"""
        old_size = self._size
        self._size = max(self._min_size, self._size - self._step)
        if old_size != self._size:
            logger.debug(f"Circle cursor size decreased to {self._size}px")
            self.update()
    
    def show(self):
        """원형 커서 표시 - 오버라이드하여 디버그 로그 추가"""
        super().show()
        logger.debug("CircleCursor.show() called explicitly")
        
    def hide(self):
        """원형 커서 숨김 - 오버라이드하여 디버그 로그 추가"""
        super().hide()
        logger.debug("CircleCursor.hide() called explicitly")
        
    def toggle_visibility(self):
        """원형 커서 표시/숨김 토글"""
        if self.isVisible():
            self.hide()
            logger.debug("Circle cursor hidden via toggle")
        else:
            self.show()
            logger.debug("Circle cursor shown via toggle") 
