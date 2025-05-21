# src/ui/settings_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QColorDialog, QSlider, QWidget, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor, QPalette
from .overlay_widget import OverlayWidget

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        flags = self.windowFlags()
        flags &= ~Qt.WindowType.Tool
        flags |= Qt.WindowType.Window
        self.setWindowFlags(flags)
        self.resize(450, 450)  # 창 크기 확대

        self.settings = QSettings()
        main_layout = QVBoxLayout(self)

        # 기존 설정 섹션 (펜 두께, 하이라이트 불투명도 등)
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QVBoxLayout(basic_group)

        # Pen size
        pen_layout = QHBoxLayout()
        pen_layout.addWidget(QLabel("Pen Thickness:"))
        self.pen_width_spin = QSpinBox()
        self.pen_width_spin.setRange(1, 20)
        self.pen_width_spin.setValue(self.settings.value("pen/width", 3, int))
        pen_layout.addWidget(self.pen_width_spin)
        basic_layout.addLayout(pen_layout)

        # Highlight opacity
        hl_layout = QHBoxLayout()
        hl_layout.addWidget(QLabel("Highlight Opacity:"))
        self.hl_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.hl_opacity_slider.setRange(1, 255)
        self.hl_opacity_slider.setValue(self.settings.value("highlight/opacity", 64, int))
        hl_layout.addWidget(self.hl_opacity_slider)
        basic_layout.addLayout(hl_layout)

        # Highlight thickness
        hlw_layout = QHBoxLayout()
        hlw_layout.addWidget(QLabel("Highlight Thickness:"))
        self.hl_width_spin = QSpinBox()
        self.hl_width_spin.setRange(1, 50)
        self.hl_width_spin.setValue(self.settings.value("highlight/width", 20, int))
        hlw_layout.addWidget(self.hl_width_spin)
        basic_layout.addLayout(hlw_layout)

        # Circular cursor color
        cursor_layout = QHBoxLayout()
        cursor_layout.addWidget(QLabel("Circular Cursor Color:"))
        self.cursor_color_btn = QPushButton("Select")
        self.set_button_color(self.cursor_color_btn, self.settings.value("cursor/color", QColor(0,120,215), type=QColor))
        cursor_layout.addWidget(self.cursor_color_btn)
        basic_layout.addLayout(cursor_layout)

        # Click effect color
        click_effect_layout = QHBoxLayout()
        click_effect_layout.addWidget(QLabel("Click Effect Color:"))
        self.click_effect_color_btn = QPushButton("Select")
        self.set_button_color(self.click_effect_color_btn, self.settings.value("click_effect/color", QColor(255,255,255), type=QColor))
        click_effect_layout.addWidget(self.click_effect_color_btn)
        basic_layout.addLayout(click_effect_layout)

        # Subtitle size
        subsize_layout = QHBoxLayout()
        subsize_layout.addWidget(QLabel("Subtitle Font Size:"))
        self.sub_font_spin = QSpinBox()
        self.sub_font_spin.setRange(10, 100)
        self.sub_font_spin.setValue(self.settings.value("subtitle/fontsize", 50, int))
        subsize_layout.addWidget(self.sub_font_spin)
        basic_layout.addLayout(subsize_layout)

        # Subtitle background color
        subbg_layout = QHBoxLayout()
        subbg_layout.addWidget(QLabel("Subtitle Background Color:"))
        self.subbg_btn = QPushButton("Select")
        self.set_button_color(self.subbg_btn, self.settings.value("subtitle/bgcolor", QColor(60,60,60,217), type=QColor))
        subbg_layout.addWidget(self.subbg_btn)
        basic_layout.addLayout(subbg_layout)

        main_layout.addWidget(basic_group)

        # 새로운 숫자키 설정 섹션 (1-6 숫자키)
        keys_group = QGroupBox("Pen & Highlight Colors (Number Keys)")
        keys_layout = QGridLayout(keys_group)

        # Pen 색상들 (1-3 번 키)
        keys_layout.addWidget(QLabel("Pen 1 (key 1):"), 0, 0)
        self.pen1_btn = QPushButton("Select")
        self.set_button_color(self.pen1_btn, self.settings.value("pen/color1", QColor(255,0,0), type=QColor))
        keys_layout.addWidget(self.pen1_btn, 0, 1)

        keys_layout.addWidget(QLabel("Pen 2 (key 2):"), 1, 0)
        self.pen2_btn = QPushButton("Select")
        self.set_button_color(self.pen2_btn, self.settings.value("pen/color2", QColor(0,255,0), type=QColor))
        keys_layout.addWidget(self.pen2_btn, 1, 1)

        keys_layout.addWidget(QLabel("Pen 3 (key 3):"), 2, 0)
        self.pen3_btn = QPushButton("Select")
        self.set_button_color(self.pen3_btn, self.settings.value("pen/color3", QColor(0,0,255), type=QColor))
        keys_layout.addWidget(self.pen3_btn, 2, 1)

        # Highlight 색상들 (4-6 번 키)
        keys_layout.addWidget(QLabel("Highlight 1 (key 4):"), 0, 2)
        self.hl1_btn = QPushButton("Select")
        self.set_button_color(self.hl1_btn, self.settings.value("highlight/color1", QColor(255,255,0,64), type=QColor))
        keys_layout.addWidget(self.hl1_btn, 0, 3)

        keys_layout.addWidget(QLabel("Highlight 2 (key 5):"), 1, 2)
        self.hl2_btn = QPushButton("Select")
        self.set_button_color(self.hl2_btn, self.settings.value("highlight/color2", QColor(144,238,144,64), type=QColor))
        keys_layout.addWidget(self.hl2_btn, 1, 3)

        keys_layout.addWidget(QLabel("Highlight 3 (key 6):"), 2, 2)
        self.hl3_btn = QPushButton("Select")
        self.set_button_color(self.hl3_btn, self.settings.value("highlight/color3", QColor(255,105,180,64), type=QColor))
        keys_layout.addWidget(self.hl3_btn, 2, 3)

        main_layout.addWidget(keys_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        reset_btn = QPushButton("Default Settings")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(reset_btn)
        main_layout.addLayout(btn_layout)

        # Signals
        self.cursor_color_btn.clicked.connect(self.pick_cursor_color)
        self.subbg_btn.clicked.connect(self.pick_subbg_color)
        self.click_effect_color_btn.clicked.connect(self.pick_click_effect_color)
        save_btn.clicked.connect(self.apply_and_close)
        reset_btn.clicked.connect(self.reset_defaults)

        # 숫자키 색상 선택 시그널
        self.pen1_btn.clicked.connect(lambda: self.pick_pen_color_num(1))
        self.pen2_btn.clicked.connect(lambda: self.pick_pen_color_num(2))
        self.pen3_btn.clicked.connect(lambda: self.pick_pen_color_num(3))
        self.hl1_btn.clicked.connect(lambda: self.pick_hl_color_num(1))
        self.hl2_btn.clicked.connect(lambda: self.pick_hl_color_num(2))
        self.hl3_btn.clicked.connect(lambda: self.pick_hl_color_num(3))

    def set_button_color(self, button, color):
        """버튼 배경색을 설정된 색상으로 표시"""
        if not color.isValid():
            return
            
        # 스타일시트로 버튼 배경색 설정
        r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()
        
        # 배경색 설정 (투명도도 표현)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({r}, {g}, {b}, {a/255});
                border: 1px solid #777;
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: rgba({r}, {g}, {b}, {min(a+30, 255)/255});
            }}
        """)
        
        # 색상이 어두운 경우 텍스트 색상을 흰색으로 변경
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        if brightness < 128:
            button.setStyleSheet(button.styleSheet() + """
                QPushButton {
                    color: white;
                }
            """)
        else:
            button.setStyleSheet(button.styleSheet() + """
                QPushButton {
                    color: black;
                }
            """)

    def pick_cursor_color(self):
        col = QColorDialog.getColor(self.settings.value("cursor/color", QColor(0,120,215), type=QColor), self)
        if col.isValid():
            self.settings.setValue("cursor/color", col)
            
            # 버튼 색상 업데이트
            self.set_button_color(self.cursor_color_btn, col)
            
            # 즉시 적용: 부모 창의 원형 커서 색상 업데이트
            parent = self.parent()
            if parent and hasattr(parent, 'circle_cursor') and parent.circle_cursor:
                # 원본 불투명도 유지 (원형 커서는 반투명)
                opacity = parent.circle_cursor._opacity
                new_color = QColor(col)
                new_color.setAlpha(int(255 * opacity))
                parent.circle_cursor.color = new_color
                
                # 화면 강제 갱신
                parent.circle_cursor.update()

    def pick_subbg_color(self):
        col = QColorDialog.getColor(self.settings.value("subtitle/bgcolor", QColor(60,60,60,217), type=QColor), self)
        if col.isValid():
            self.settings.setValue("subtitle/bgcolor", col)
            # 버튼 색상 업데이트
            self.set_button_color(self.subbg_btn, col)
            
            # 즉시 적용: 부모 창의 overlay 배경색 업데이트
            parent = self.parent()
            if parent and hasattr(parent, 'overlay'):
                # 배경색 업데이트 - rgba 형식 사용
                r, g, b, a = col.red(), col.green(), col.blue(), col.alpha()
                bg_style = f"rgba({r}, {g}, {b}, {a/255})"
                
                # overlay 직접 접근
                parent.overlay.BG_STYLE = bg_style
                
                # 기존 카드 스타일 업데이트
                if hasattr(parent.overlay, 'update_card_styles'):
                    parent.overlay.update_card_styles()
                else:
                    # update_card_styles 메서드가 없는 경우, 카드 스타일 직접 업데이트
                    update_overlay_cards(parent.overlay, bg_style)

    def pick_click_effect_color(self):
        col = QColorDialog.getColor(self.settings.value("click_effect/color", QColor(255,255,255), type=QColor), self)
        if col.isValid():
            self.settings.setValue("click_effect/color", col)
            # 버튼 색상 업데이트
            self.set_button_color(self.click_effect_color_btn, col)

    def pick_pen_color_num(self, num):
        """숫자키 펜 색상 선택"""
        default_colors = {
            1: QColor(255, 0, 0),       # 빨강
            2: QColor(0, 255, 0),       # 초록
            3: QColor(0, 0, 255),       # 파랑
        }
        
        current = self.settings.value(f"pen/color{num}", default_colors[num], type=QColor)
        col = QColorDialog.getColor(current, self)
        if col.isValid():
            self.settings.setValue(f"pen/color{num}", col)
            
            # 버튼 색상 업데이트
            btn = getattr(self, f"pen{num}_btn")
            self.set_button_color(btn, col)

    def pick_hl_color_num(self, num):
        """숫자키 하이라이트 색상 선택"""
        default_colors = {
            1: QColor(255, 255, 0),     # 노랑
            2: QColor(144, 238, 144),   # 연두색
            3: QColor(255, 105, 180),   # 핑크
        }
        
        # 하이라이트 색상의 투명도는 유지하면서 색상만 변경
        alpha = self.settings.value("highlight/opacity", 64, int)
        current = self.settings.value(f"highlight/color{num}", default_colors[num], type=QColor)
        
        col = QColorDialog.getColor(current, self)
        if col.isValid():
            # 기존 투명도 유지
            col.setAlpha(alpha)
            self.settings.setValue(f"highlight/color{num}", col)
            
            # 버튼 색상 업데이트 (투명도 적용)
            btn = getattr(self, f"hl{num}_btn")
            self.set_button_color(btn, col)

    def apply_and_close(self):
        # Save
        self.settings.setValue("pen/width", self.pen_width_spin.value())
        self.settings.setValue("highlight/opacity", self.hl_opacity_slider.value())
        self.settings.setValue("highlight/width", self.hl_width_spin.value())
        self.settings.setValue("subtitle/fontsize", self.sub_font_spin.value())
        
        # 하이라이트 색상들 투명도 업데이트
        alpha = self.hl_opacity_slider.value()
        for i in range(1, 4):
            col = self.settings.value(f"highlight/color{i}", None, type=QColor)
            if col:
                col.setAlpha(alpha)
                self.settings.setValue(f"highlight/color{i}", col)
                
                # 버튼 색상 업데이트 (투명도 변경됨)
                btn = getattr(self, f"hl{i}_btn")
                self.set_button_color(btn, col)
        
        # 자막 배경색 및 폰트 크기 즉시 적용
        parent = self.parent()
        if parent and hasattr(parent, 'overlay'):
            # 설정값 불러오기
            fs = self.sub_font_spin.value()
            bgcol = self.settings.value("subtitle/bgcolor", QColor(60,60,60,217), type=QColor)
            
            # overlay 속성 직접 업데이트
            parent.overlay.FONT_SIZE = fs
            
            # rgba 형식 사용
            r, g, b, a = bgcol.red(), bgcol.green(), bgcol.blue(), bgcol.alpha()
            bg_style = f"rgba({r}, {g}, {b}, {a/255})"
            parent.overlay.BG_STYLE = bg_style
            
            # 카드 스타일 업데이트
            if hasattr(parent.overlay, 'update_card_styles'):
                parent.overlay.update_card_styles()
            else:
                # update_card_styles 메서드가 없는 경우, 카드 스타일 직접 업데이트
                update_overlay_cards(parent.overlay, bg_style)
        
        # Apply immediately: notify parent window
        self.parent().load_settings()
        self.accept()

    def reset_defaults(self):
        # Restore default values
        defaults = {
            "pen/width": 3,
            "pen/color1": QColor(255, 0, 0),      # 빨강
            "pen/color2": QColor(0, 255, 0),      # 초록
            "pen/color3": QColor(0, 0, 255),      # 파랑
            "highlight/width": 20,
            "highlight/opacity": 64,
            "highlight/color1": QColor(255, 255, 0, 64),   # 노랑
            "highlight/color2": QColor(144, 238, 144, 64), # 연두색
            "highlight/color3": QColor(255, 105, 180, 64), # 핑크
            "subtitle/fontsize": 50,
            "cursor/color": QColor(0, 120, 215),
            "subtitle/bgcolor": QColor(60, 60, 60, 217),
            "click_effect/color": QColor(255, 255, 255)
        }
        for k, v in defaults.items():
            self.settings.setValue(k, v)
            
        # Update UI as well
        self.pen_width_spin.setValue(defaults["pen/width"])
        self.hl_opacity_slider.setValue(defaults["highlight/opacity"])
        self.hl_width_spin.setValue(defaults["highlight/width"])
        self.sub_font_spin.setValue(defaults["subtitle/fontsize"])
        
        # 모든 버튼 색상 업데이트
        self.set_button_color(self.cursor_color_btn, defaults["cursor/color"])
        self.set_button_color(self.subbg_btn, defaults["subtitle/bgcolor"])
        self.set_button_color(self.click_effect_color_btn, defaults["click_effect/color"])
        
        # 숫자키 색상 버튼 업데이트
        for i in range(1, 4):
            btn = getattr(self, f"pen{i}_btn")
            self.set_button_color(btn, defaults[f"pen/color{i}"])
            
            btn = getattr(self, f"hl{i}_btn")
            self.set_button_color(btn, defaults[f"highlight/color{i}"])
        
        # 원형 커서 색상 즉시 적용
        parent = self.parent()
        if parent:
            if hasattr(parent, 'circle_cursor') and parent.circle_cursor:
                # 기본 색상 적용 (불투명도는 setter에서 자동 적용)
                parent.circle_cursor.color = defaults["cursor/color"]
                parent.circle_cursor.update()
                
            # 자막 배경색 즉시 적용
            if hasattr(parent, 'overlay'):
                # 자막 폰트 크기 설정
                parent.overlay.FONT_SIZE = defaults["subtitle/fontsize"]
                
                # 자막 배경색 설정 - rgba 형식으로 직접 지정
                bgcol = defaults["subtitle/bgcolor"]
                r, g, b, a = bgcol.red(), bgcol.green(), bgcol.blue(), bgcol.alpha()
                bg_style = f"rgba({r}, {g}, {b}, {a/255})"
                parent.overlay.BG_STYLE = bg_style
                
                # 강제로 현재 자막 업데이트
                update_overlay_cards(parent.overlay, bg_style)
                
                # 무조건 로드해서 모든 설정 즉시 적용
                parent.load_settings()

def update_overlay_cards(overlay, bg_style):
    """OverlayWidget의 기존 카드 스타일을 업데이트"""
    if not hasattr(overlay, 'cards') or not overlay.cards:
        return
        
    for card in overlay.cards:
        # 현재 설정된 배경색과 폰트 크기로 스타일 업데이트
        card.setStyleSheet(f"""
            QLabel {{
                color: white;
                background: {bg_style};
                border-radius: 16px;
                min-width: 64px;
                min-height: 120px;
                font-size: {overlay.FONT_SIZE}px;
                font-weight: 500;
                padding: 0 18px;
                qproperty-alignment: AlignCenter;
            }}
        """)
    
    # 화면 갱신
    overlay.update()
