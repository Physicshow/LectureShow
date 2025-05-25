from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QPoint, Qt
import time
import logging

logger = logging.getLogger(__name__)

MODIFIER_KEYS = {
    'alt': 'Alt', 'alt_gr': 'Alt', 'alt_l': 'Alt', 'alt_r': 'Alt',
    'ctrl': 'Ctrl', 'ctrl_l': 'Ctrl', 'ctrl_r': 'Ctrl',
    'shift': 'Shift', 'shift_l': 'Shift', 'shift_r': 'Shift',
    'cmd': 'Win', 'cmd_l': 'Win', 'cmd_r': 'Win',
    'win': 'Win', 'win_l': 'Win', 'win_r': 'Win'
}

FKEYS = {
    'f1': 1, 'f2': 2, 'f3': 3, 'f4': 4, 'f5': 5, 
    'f6': 6, 'f7': 7, 'f8': 8, 'f9': 9, 'f10': 10,
    'f11': 11, 'f12': 12
}

SPECIAL_KEY_MAP = {
    '<21>': 'KO/EN',
    'hangul': 'KO/EN',
    'hanja': 'Hanja',
    'left': '←',
    'right': '→',
    'up': '↑',
    'down': '↓'
}

# Keyboard number key code mapping
NUMBER_KEYS = {
    # Virtual key codes (VK)
    49: '1', 50: '2', 51: '3', 52: '4', 53: '5', 54: '6', 55: '7', 56: '8', 57: '9', 48: '0',
    # Key name mapping
    '1': '1', '2': '2', '3': '3', '4': '4', '5': '5',
    '6': '6', '7': '7', '8': '8', '9': '9', '0': '0',
    # NumPad keys
    'num_1': '1', 'num_2': '2', 'num_3': '3', 'num_4': '4', 'num_5': '5',
    'num_6': '6', 'num_7': '7', 'num_8': '8', 'num_9': '9', 'num_0': '0'
}

# Keyboard shortcut mapping
KEYBOARD_SHORTCUTS = {
    "ctrl+1": "activate_zoom", # Ctrl+1: Activate screen capture and zoom function
    "ctrl+shift++": "increase_circle_cursor", # Ctrl+Shift++: Increase circular cursor size
    "ctrl+shift+=": "increase_circle_cursor", # Ctrl+Shift+=: Increase circular cursor size
    "ctrl+shift+-": "decrease_circle_cursor" # Ctrl+Shift+-: Decrease circular cursor size
}

MODIFIER_RELEASE_THRESHOLD = 0.2 # In seconds (200ms)

class InputListener(QObject):
    input_detected = pyqtSignal(str)
    position_changed = pyqtSignal(str)
    mouse_clicked = pyqtSignal(int, int)
    mouse_down = pyqtSignal(int, int, str)
    mouse_move = pyqtSignal(int, int)
    mouse_up = pyqtSignal(int, int, str)
    scroll_effect = pyqtSignal(int, int, str)
    show_modifier = pyqtSignal(str)
    activate_zoom = pyqtSignal()
    toggle_circle_cursor = pyqtSignal()
    increase_circle_cursor = pyqtSignal()
    decrease_circle_cursor = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.keyboard_listener = None
        self.mouse_listener = None
        self.modifiers = set()
        self.last_key_time = 0
        self.key_buffer = []
        self.is_dragging = False
        self.is_right_dragging = False
        
        # Variables for scroll event aggregation
        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.emit_scroll_event)
        self.scroll_direction = None
        self.scroll_count = 0
        self.scroll_debounce_time = 300
        
        # Variables for modifier key display control
        self.modifier_timer = QTimer()
        self.modifier_timer.setSingleShot(True)
        self.modifier_timer.timeout.connect(self.update_modifier_display)
        self.last_modifier_set = set()
        self.modifier_changed = False
        
        # Timer for resetting modifier key states
        self.reset_modifier_timer = QTimer()
        self.reset_modifier_timer.setSingleShot(True)
        self.reset_modifier_timer.timeout.connect(self.reset_modifiers)
        self.reset_modifier_timer.start(2000)  # Check every 2 seconds
        
        logger.info("InputListener initialized")
        
    def start(self):
        # Start pynput listeners
        try:
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.keyboard_listener.start()
            self.mouse_listener = mouse.Listener(
                on_click=self.on_mouse_click,
                on_scroll=self.on_mouse_scroll,
                on_move=self.on_mouse_move
            )
            self.mouse_listener.start()
            logger.info("pynput keyboard and mouse listeners started")
        except Exception as e:
            logger.error(f"Failed to start pynput listeners: {e}")
        
    def on_key_press(self, key):
        key_name = self._key_to_name(key)
        char = getattr(key, 'char', None)
        ord_char = ord(char) if char and isinstance(char, str) and len(char) == 1 else None
        
        # Add modifier key to modifiers set if pressed
        if self._is_modifier(key_name):
            if key_name.lower() in ['ctrl', 'ctrl_l', 'ctrl_r']:
                self.modifiers.add('ctrl')
            elif key_name.lower() in ['shift', 'shift_l', 'shift_r']:
                self.modifiers.add('shift')
            elif key_name.lower() in ['alt', 'alt_l', 'alt_r']:
                self.modifiers.add('alt')
            elif key_name.lower() in ['win', 'win_l', 'win_r', 'cmd', 'cmd_l', 'cmd_r']:
                self.modifiers.add('win')
        
        # Check which modifier keys are currently pressed
        modifiers_pressed = []
        if self._is_ctrl_pressed():
            modifiers_pressed.append("Ctrl")
        if self._is_shift_pressed():
            modifiers_pressed.append("Shift")
        if self._is_alt_pressed():
            modifiers_pressed.append("Alt")
        if self._is_win_pressed():
            modifiers_pressed.append("Win")
        
        # Terminate processing here if only modifier key was pressed
        if self._is_modifier(key_name):
            old_modifiers = self.modifiers.copy()
            
            # Update timer and display if modifier key state has changed
            if old_modifiers != self.modifiers:
                self.modifier_changed = True
                self.update_modifier_display()
            
            # 여기에 추가: 단독 modifier 키도 input_detected 시그널 발생
            mod_text = '+'.join(self._get_modifiers())
            if mod_text:
                self.input_detected.emit(mod_text)
            
            self.last_key_time = time.time()
            return
        
        # Special handling for Ctrl+number key detection
        is_ctrl_pressed = self._is_ctrl_pressed()
        is_shift_pressed = self._is_shift_pressed()
        
        # Plus (+) key detection - Handle Ctrl+Shift++ shortcut
        if is_ctrl_pressed and is_shift_pressed and (
            key_name == '+' or 
            key_name == '=' or 
            (hasattr(key, 'vk') and key.vk == 107) or  # NumPad + 
            (hasattr(key, 'vk') and key.vk == 187)     # Regular keyboard =
        ):
            self.increase_circle_cursor.emit()
            combo = "Ctrl+Shift++"
            self.input_detected.emit(combo)
            self.last_key_time = time.time()
            return
        
        # Minus (-) key detection - Handle Ctrl+Shift+- shortcut
        if is_ctrl_pressed and is_shift_pressed and (
            key_name == '-' or 
            (hasattr(key, 'vk') and key.vk == 109) or  # NumPad -
            (hasattr(key, 'vk') and key.vk == 189)     # Regular keyboard -
        ):
            self.decrease_circle_cursor.emit()
            combo = "Ctrl+Shift+-"
            self.input_detected.emit(combo)
            self.last_key_time = time.time()
            return
        
        # Number 1 key detection - Handle Ctrl+1 shortcut
        if is_ctrl_pressed and not is_shift_pressed and (
            self._is_key_number_1(key, key_name) or 
            (hasattr(key, 'vk') and key.vk == 49) or  # Keyboard 1
            key_name == '1'
        ):
            self.activate_zoom.emit()
            combo = "Ctrl+1"
            self.input_detected.emit(combo)
            self.last_key_time = time.time()
            return
        
        # General key processing
        if self._is_ctrl_pressed() and hasattr(key, 'char') and key.char and 1 <= ord(key.char) <= 26:
            char_alpha = chr(ord('a') + ord(key.char) - 1)
            combo = self._format_combo(char_alpha)
        else:
            combo = self._format_combo(key_name)
        
        # Shortcut processing
        combo_lower = combo.lower()
        if combo_lower in KEYBOARD_SHORTCUTS:
            action = KEYBOARD_SHORTCUTS[combo_lower]
            
            # Execute action based on shortcut
            if action == "activate_zoom":
                # Explicitly check if it's Ctrl+1
                if combo_lower == "ctrl+1":
                    self.activate_zoom.emit()
            elif action == "toggle_circle_cursor":
                self.toggle_circle_cursor.emit()
            elif action == "increase_circle_cursor":
                self.increase_circle_cursor.emit()
            elif action == "decrease_circle_cursor":
                self.decrease_circle_cursor.emit()
        
        # Input detection signal transmission
        self.input_detected.emit(combo)
        self.last_key_time = time.time()
        
    def on_key_release(self, key):
        key_name = self._key_to_name(key)
        print(f"[DEBUG] key_release object: {key}, key_name: {key_name!r}")
        
        # 수정: modifier 키가 떼어졌을 때 self.modifiers에서 제거
        if self._is_modifier(key_name):
            if key_name.lower() in ['ctrl', 'ctrl_l', 'ctrl_r']:
                self.modifiers.discard('ctrl')
            elif key_name.lower() in ['shift', 'shift_l', 'shift_r']:
                self.modifiers.discard('shift')
            elif key_name.lower() in ['alt', 'alt_l', 'alt_r']:
                self.modifiers.discard('alt')
            elif key_name.lower() in ['win', 'win_l', 'win_r', 'cmd', 'cmd_l', 'cmd_r']:
                self.modifiers.discard('win')
            
            # 상태가 변경되었음을 표시
            self.modifier_changed = True
            self.update_modifier_display()
    
    def on_mouse_click(self, x, y, button, pressed):
        button_name = str(button).replace('Button.', '').capitalize()
        button_type = "left" if button == mouse.Button.left else "right" if button == mouse.Button.right else "other"
        
        if button in (mouse.Button.left, mouse.Button.right):
            if pressed:
                if button == mouse.Button.left:
                    self.is_dragging = True
                else:
                    self.is_right_dragging = True
                    
                combo = self._format_combo(f"Mouse {button_name}")
                self.input_detected.emit(combo)
                self.mouse_down.emit(x, y, button_type)
                print(f"[DEBUG] Mouse {button_type} down at ({x}, {y})")
            else:
                if button == mouse.Button.left:
                    self.is_dragging = False
                else:
                    self.is_right_dragging = False
                    
                self.mouse_up.emit(x, y, button_type)
                print(f"[DEBUG] Mouse {button_type} up at ({x}, {y})")
        else:
            if pressed:
                combo = self._format_combo(f"Mouse {button_name}")
                self.input_detected.emit(combo)
                self.mouse_clicked.emit(x, y)
                print(f"[DEBUG] Mouse {button_name} click at ({x}, {y})")
        
    def on_mouse_scroll(self, x, y, dx, dy):
        # Scroll direction determination
        direction = "up" if dy > 0 else "down"
        
        # Scroll effect generation
        self.scroll_effect.emit(x, y, direction)
        
        # --- Scroll input processing logic addition ---
        current_time = time.time()
        
        # Start new if previous scroll direction is different or timer has expired
        if self.scroll_direction != direction or current_time - self.last_key_time > self.scroll_debounce_time / 1000.0:
            # Emit existing scroll events if any
            if self.scroll_count > 0:
                self.emit_scroll_event()
            
            # Start new
            self.scroll_direction = direction
            self.scroll_count = 1
        else:
            # Continuous scroll count increase
            self.scroll_count += 1

        # Last input time update and timer start
        self.last_key_time = current_time
        QTimer.singleShot(0, lambda: self.scroll_timer.start(self.scroll_debounce_time))
        # --- Scroll input processing logic end ---
        
        # Current modifier key state check and update (Ctrl+Scroll, etc.)
        if self.modifiers:
            self.update_modifier_display()
    
    def emit_scroll_event(self):
        """Emit accumulated scroll events."""
        if self.scroll_direction and self.scroll_count > 0:
            # Emit scroll count if greater than 1
            if self.scroll_count > 1:
                direction = f"{self.scroll_direction} x{self.scroll_count}"
            else:
                direction = self.scroll_direction
                
        combo = self._format_combo(direction)
        self.input_detected.emit(combo)
            
        # Reset state
        self.scroll_direction = None
        self.scroll_count = 0
    
    def on_mouse_move(self, x, y):
        # Always emit mouse movement signal (for circular cursor, etc.)
        self.mouse_move.emit(x, y)
        
        # Drag state logging (for debugging)
        if self.is_dragging:
            # print(f"[DEBUG] Mouse left dragging to ({x}, {y})")
            pass
        elif self.is_right_dragging:
            # print(f"[DEBUG] Mouse right dragging to ({x}, {y})")
            pass
        
    def _is_modifier(self, key_name):
        """
        Check if given key name is a modifier key.
        """
        if not key_name:
            return False
            
        key_name_lower = key_name.lower()
        
        # Direct check of keys in MODIFIER_KEYS dictionary
        if key_name_lower in MODIFIER_KEYS:
            return True
            
        # Check for modifier keys with suffixes (e.g., ctrl_l, control_r) - This part can be kept
        if key_name_lower in ('ctrl', 'ctrl_l', 'ctrl_r', 'control', 'control_l', 'control_r'):
            return True
        if key_name_lower in ('shift', 'shift_l', 'shift_r'):
            return True
        if key_name_lower in ('alt', 'alt_l', 'alt_r', 'alt_gr'):
            return True
        if key_name_lower in ('win', 'win_l', 'win_r', 'cmd', 'cmd_l', 'cmd_r', 'super', 'super_l', 'super_r'):
                return True
            
        return False
    
    def _is_win_pressed(self):
        """Check if Win/Super key is pressed"""
        return 'win' in self.modifiers
    
    def _is_ctrl_pressed(self):
        """Check if Ctrl key is pressed"""
        return 'ctrl' in self.modifiers
    
    def _is_shift_pressed(self):
        """Check if Shift key is pressed"""
        return 'shift' in self.modifiers
    
    def _is_alt_pressed(self):
        """Check if Alt key is pressed"""
        return 'alt' in self.modifiers
    
    def _get_modifiers(self):
        order = ['ctrl', 'shift', 'alt', 'win']
        result = []
        for mod in order:
            # Direct check for standard modifier names in self.modifiers set
            if mod in self.modifiers: 
                    result.append(mod.capitalize() if mod != 'win' else 'Win')
        return result
    
    def _format_combo(self, main):
        mods = self._get_modifiers()
        # main is None or empty string, but if there's any modifier, show modifier only
        if not main:
            return '+'.join(mods) if mods else ''
        if mods:
            return '+'.join(mods + [main])
        else:
            return main
    
    def _key_to_name(self, key):
        # Special key mapping for Korean/English
        try:
            if hasattr(key, 'vk') and str(key.vk) == '21':
                return 'KO/EN'
        except Exception:
            pass
        try:
            if hasattr(key, 'name') and key.name in SPECIAL_KEY_MAP:
                return SPECIAL_KEY_MAP[key.name]
        except Exception:
            pass
        try:
            if hasattr(key, 'char') and key.char:
                # Return number keys directly
                if key.char in '0123456789':
                    print(f"[DEBUG] Number key detected: {key.char!r}")
                    return key.char
                # Return empty string for control characters (ASCII 1~26)
                if 1 <= ord(key.char) <= 26:
                    return ''
                return key.char
        except Exception as e:
            print(f"[DEBUG] _key_to_name processing exception: {e}")
            pass
        s = str(key).replace('Key.', '').lower()
        
        # Check if it's a number key (KeyboardListener may handle differently)
        if s in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0'):
            print(f"[DEBUG] String-based number key detection: {s!r}")
            return s
            
        # modifier unification
        if s in ('ctrl_l', 'ctrl_r'):
            return 'ctrl'
        if s in ('shift_l', 'shift_r'):
            return 'shift'
        if s in ('alt_l', 'alt_r'):
            return 'alt'
        if s in ('super_l', 'super_r', 'cmd', 'win'):
            return 'win'
        if s in SPECIAL_KEY_MAP:
            return SPECIAL_KEY_MAP[s]
        if s.startswith('<') and s.endswith('>') and s[1:-1].isdigit():
            if s == '<21>':
                return 'KO/EN'
            return ''
        return s
    
    def _is_single_ascii_ctrl_combo(self, key):
        # Check if it's a ctrl+alphabet combination
        try:
            if hasattr(key, 'char') and key.char and 1 <= ord(key.char) <= 26:
                return True
        except Exception:
            pass
        return False
    
    def _ctrl_combo_to_alpha(self, key):
        # Convert ctrl+alphabet combination to human readable format
        try:
            if hasattr(key, 'char') and key.char and 1 <= ord(key.char) <= 26:
                # chr(1) = Ctrl+A, chr(2) = Ctrl+B, ...
                return chr(ord('a') + ord(key.char) - 1)
        except Exception:
            pass
        return ''

    def update_display(self):
        if self.key_buffer:
            text = " + ".join(self.key_buffer)
            self.input_detected.emit(text)
            self.key_buffer = [] 

    def update_modifier_display(self):
        """Display modifier key state on screen."""
        # Get current modifier key combination
        mods = self._get_modifiers()
        mod_text = '+'.join(mods) if mods else ""
        
        # 수정: modifier_changed 확인 조건 제거
        if self.last_modifier_set != set(mods):
            self.modifier_changed = False
            self.last_modifier_set = set(mods)
            if mod_text:
                # Display only when there's a modifier
                self.show_modifier.emit(mod_text)
                # Automatic timer to hide (won't show if CTRL is held down)
                QTimer.singleShot(0, lambda: self.modifier_timer.start(1000))

    def _is_key_number_1(self, key, key_name=None):
        """Check if key is number 1 in various ways"""
        if key_name is None:
            key_name = self._key_to_name(key)
            
        # Check number key 1 in various ways
        if key_name == '1':
            print(f"[DEBUG] key_name-based number key 1 detected")
            return True
        elif str(key) == 'Key.1':
            print(f"[DEBUG] str(key)=='Key.1' based number key 1 detected")
            return True
        elif hasattr(key, 'char') and key.char == '1':
            print(f"[DEBUG] key.char based number key 1 detected")
            return True
        elif hasattr(key, 'vk') and key.vk == 49:  # 49 is virtual key code for keyboard number 1
            print(f"[DEBUG] key.vk based number key 1 detected: {key.vk}")
            return True
        elif hasattr(key, 'vk') and key.vk == 97:  # 97 is virtual key code for number pad 1
            print(f"[DEBUG] number pad key.vk based number key 1 detected: {key.vk}")
            return True
        elif hasattr(key, 'vk') and key.vk in NUMBER_KEYS and NUMBER_KEYS[key.vk] == '1':
            print(f"[DEBUG] NUMBER_KEYS based number key 1 detected: {key.vk}")
            return True
        
        return False 

    def reset_modifiers(self):
        """Check modifier key state periodically and reset if necessary"""
        import keyboard  # System keyboard state check for
        
        # Actual keyboard state check
        ctrl_pressed = keyboard.is_pressed('ctrl')
        shift_pressed = keyboard.is_pressed('shift')
        alt_pressed = keyboard.is_pressed('alt')
        
        # Compare actual state with stored state and modify
        if 'ctrl' in self.modifiers and not ctrl_pressed:
            self.modifiers.discard('ctrl')
            self.modifier_changed = True
        
        if 'shift' in self.modifiers and not shift_pressed:
            self.modifiers.discard('shift')
            self.modifier_changed = True
        
        if 'alt' in self.modifiers and not alt_pressed:
            self.modifiers.discard('alt')
            self.modifier_changed = True
        
        if self.modifier_changed:
            self.update_modifier_display()
        
        # Timer restart
        QTimer.singleShot(0, lambda: self.reset_modifier_timer.start(2000))
