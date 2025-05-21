from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QPoint
from PyQt6.QtGui import QColor
from .click_effect import ClickEffectWidget
import logging

logger = logging.getLogger(__name__)

CARD_MARGIN = 12
CARD_SPACING = 16
CARD_HEIGHT = 120
CARD_MIN_WIDTH = 64
CARD_BG = 'rgba(60, 60, 60, 0.85)'
CARD_RADIUS = 16
CARD_FONT_SIZE = 50
SLIDE_MARGIN_X = 32
SLIDE_MARGIN_Y = 32
DISPLAY_DURATION = 2200  # ms

class OverlayWidget(QWidget):
    FONT_SIZE = CARD_FONT_SIZE
    BG_STYLE = CARD_BG

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Allow mouse events to pass through
        
        # 윈도우 플래그에 Tool 추가 - 작업 표시줄에 나타나지 않음
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        self.setFixedHeight(CARD_HEIGHT + CARD_MARGIN * 2)

        self.cards = []
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        self.layout.setSpacing(CARD_SPACING)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.slide_out)

        self.animation = QPropertyAnimation(self, b"geometry")
        self.is_visible = False
        self._anim_disconnect = False
        self.position = "left"  # Default: bottom left

        logger.debug("OverlayWidget initialized")

    def set_position(self, pos):
        if pos in ("left", "right"):
            self.position = pos
            # Immediately reposition current overlay if visible
            if self.is_visible:
                self.slide_in()

    def show_input(self, text):
        # Remove existing cards
        for card in self.cards:
            self.layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

        # Split multiple keys/commands into individual cards
        for part in text.split(" + "):
            card = QLabel(part)
            card.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background: {self.BG_STYLE};
                    border-radius: {CARD_RADIUS}px;
                    min-width: {CARD_MIN_WIDTH}px;
                    min-height: {CARD_HEIGHT}px;
                    font-size: {self.FONT_SIZE}px;
                    font-weight: 500;
                    padding: 0 18px;
                    qproperty-alignment: AlignCenter;
                }}
            """)
            self.layout.addWidget(card)
            self.cards.append(card)

        self.adjustSize()
        QApplication.processEvents()  # Ensure size is finalized
        self.resize(self.sizeHint())
        if self.width() <= 1 or self.height() <= 1:
            self.resize(self.sizeHint())
            QApplication.processEvents()

        self.slide_in()
        self.hide_timer.stop()
        self.hide_timer.start(DISPLAY_DURATION)

    def slide_in(self):
        if self.animation.state() == self.animation.State.Running:
            self.animation.stop()
        if self._anim_disconnect:
            try:
                self.animation.finished.disconnect(self.hide)
            except Exception:
                pass
            self._anim_disconnect = False

        screen = QApplication.primaryScreen()
        screen_geom = screen.geometry()

        if self.position == "left":
            target_x = screen_geom.x() + SLIDE_MARGIN_X
        else:
            target_x = screen_geom.x() + screen_geom.width() - self.width() - SLIDE_MARGIN_X
        target_y = screen_geom.y() + screen_geom.height() - self.height() - SLIDE_MARGIN_Y

        if self.position == "left":
            start_rect = QRect(target_x - self.width(), target_y, self.width(), self.height())
        else:
            start_rect = QRect(target_x + self.width(), target_y, self.width(), self.height())
        end_rect = QRect(target_x, target_y, self.width(), self.height())

        self.setGeometry(start_rect)
        self.show()
        self.raise_()

        self.animation.setDuration(250)
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
        self.is_visible = True

    def slide_out(self):
        if not self.is_visible:
            return
        if self.animation.state() == self.animation.State.Running:
            self.animation.stop()

        screen = QApplication.primaryScreen()
        screen_geom = screen.geometry()

        if self.position == "left":
            target_x = screen_geom.x() + SLIDE_MARGIN_X
        else:
            target_x = screen_geom.x() + screen_geom.width() - self.width() - SLIDE_MARGIN_X
        target_y = screen_geom.y() + screen_geom.height() - self.height() - SLIDE_MARGIN_Y

        start_rect = QRect(self.x(), target_y, self.width(), self.height())
        if self.position == "left":
            end_rect = QRect(target_x - self.width(), target_y, self.width(), self.height())
        else:
            end_rect = QRect(target_x + self.width(), target_y, self.width(), self.height())

        try:
            self.animation.finished.disconnect(self.hide)
        except Exception:
            pass
        self.animation.finished.connect(self.hide)
        self._anim_disconnect = True

        self.animation.setDuration(250)
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
        self.is_visible = False

    def hide_input(self):
        self.slide_out()

    def update_card_styles(self):
        """기존 카드의 스타일을 업데이트하는 메서드"""
        if not self.cards:
            return
        
        for card in self.cards:
            # 현재 설정된 배경색과 폰트 크기로 스타일 업데이트
            card.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background: {self.BG_STYLE};
                    border-radius: {CARD_RADIUS}px;
                    min-width: {CARD_MIN_WIDTH}px;
                    min-height: {CARD_HEIGHT}px;
                    font-size: {self.FONT_SIZE}px;
                    font-weight: 500;
                    padding: 0 18px;
                    qproperty-alignment: AlignCenter;
                }}
            """)
        
        # 화면 갱신
        self.update()
