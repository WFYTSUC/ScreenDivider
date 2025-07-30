import tkinter as tk
from tkinter import messagebox
import threading
import time
import sys
import os
import json
from PIL import ImageGrab, ImageTk

class ScreenDivider:
    def __init__(self):
        # Mac不需要DPI感知设置，移除Windows特定代码
        
        self.root = tk.Tk()
        self.root.title("屏幕分割工具")
        
        # 获取屏幕尺寸
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # 设置窗口属性
        self.root.geometry(f"{self.screen_width}x20+0+{self.screen_height//2}")  # 7+6+7=20像素高度
        self.root.resizable(False, False)  # 禁止调整大小
        self.root.overrideredirect(True)  # 无边框窗口
        
        # Mac特殊设置：使用最高的窗口层级以在全屏模式下显示
        try:
            # 设置窗口为浮动面板类型，确保在全屏应用上方显示
            self.root.attributes('-type', 'utility')  # 工具窗口类型
            self.root.attributes('-topmost', True)  # 置顶
            self.root.wm_attributes('-topmost', 1)  # 强制置顶
            # 尝试设置为系统级浮动窗口
            self.root.attributes('-level', 'floating')
            # 设置为始终可见的系统窗口
            self.root.attributes('-modified', False)
        except:
            # 如果特殊属性不支持，使用标准置顶
            self.root.attributes('-topmost', True)
        
        self.root.attributes('-alpha', 0.9)  # 透明度
        
        # 绑定窗口事件，确保横杠始终可见
        self.root.bind('<FocusOut>', self.on_focus_out)
        self.root.bind('<Map>', self.on_map)
        
        # 创建主框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)
        
        # 创建上半部分灰色区域（更美观的半透明效果）
        self.upper_gray = tk.Frame(self.main_frame, height=7, bg='#E8E8E8')
        self.upper_gray.pack(fill='x')
        self.upper_gray.pack_propagate(False)
        
        # 创建画布（增加高度，更明显）
        self.canvas = tk.Canvas(self.main_frame, width=self.screen_width, height=6, 
                               bg='#4444FF', highlightthickness=0)  # 默认蓝色
        self.canvas.pack()
        
        # 创建下半部分灰色区域（更美观的半透明效果）
        self.lower_gray = tk.Frame(self.main_frame, height=7, bg='#E8E8E8')
        self.lower_gray.pack(fill='x')
        self.lower_gray.pack_propagate(False)
        
        # 状态变量
        self.is_splitting = False
        self.split_y = 0
        self.is_hovered = False
        self.upper_window = None
        self.fixed_image = None
        self.split_mode = "upper"  # "upper" 或 "lower"，默认固定上方
        
        # 加载所有设置
        settings = self.load_settings()
        self.current_language = settings['language']
        self.split_mode = settings['split_mode']
        self.current_color = settings['color']
        self.languages = {
            "zh": {
                "split": "分割",
                "restore": "恢复",
                "select_color": "选择颜色",
                "split_mode": "分割模式",
                "fix_upper": "固定上方",
                "fix_lower": "固定下方",
                "close": "关闭",
                "blue": "蓝",
                "red": "红",
                "yellow": "黄",
                "gray": "灰",
                "white": "白",
                "black": "黑",
                "language": "语言",
                "chinese": "中文",
                "english": "English",
                "error_capture": "无法捕获屏幕图像",
                "error_split": "分割屏幕时发生错误：",
                "error_restore": "恢复屏幕时发生错误：",
                "error_startup": "程序启动失败："
            },
            "en": {
                "split": "Split",
                "restore": "Restore",
                "select_color": "Select Color",
                "split_mode": "Split Mode",
                "fix_upper": "Fix Upper",
                "fix_lower": "Fix Lower",
                "close": "Close",
                "blue": "Blue",
                "red": "Red",
                "yellow": "Yellow",
                "gray": "Gray",
                "white": "White",
                "black": "Black",
                "language": "Language",
                "chinese": "中文",
                "english": "English",
                "error_capture": "Unable to capture screen image",
                "error_split": "Error occurred while splitting screen: ",
                "error_restore": "Error occurred while restoring screen: ",
                "error_startup": "Program startup failed: "
            }
        }
        
        # 颜色配置
        self.colors = {
            "blue": {"normal": "#4444FF", "hover": "#6666FF", "gradient": [(104, 104, 255), (68, 68, 255)]},
            "red": {"normal": "#FF4444", "hover": "#FF6666", "gradient": [(255, 104, 104), (255, 68, 68)]},
            "yellow": {"normal": "#FFFF44", "hover": "#FFFF66", "gradient": [(255, 255, 104), (255, 255, 68)]},
            "gray": {"normal": "#888888", "hover": "#AAAAAA", "gradient": [(136, 136, 136), (104, 104, 104)]},
            "white": {"normal": "#FFFFFF", "hover": "#EEEEEE", "gradient": [(255, 255, 255), (240, 240, 240)]},
            "black": {"normal": "#000000", "hover": "#222222", "gradient": [(40, 40, 40), (0, 0, 0)]}
        }
        
        # 应用加载的颜色设置到画布
        self.canvas.configure(bg=self.colors[self.current_color]["normal"])
        # 绘制横杠效果
        self.draw_line()
        
        # 绑定事件 - Mac上右键是Button-2，中键是Button-3
        self.canvas.bind('<Button-1>', self.start_drag)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<Button-2>', self.show_menu)  # Mac上右键是Button-2
        self.canvas.bind('<Double-Button-1>', self.show_menu)  # Mac上双指单击
        self.canvas.bind('<Control-Button-1>', self.show_menu)  # Mac上Control+单指单击
        self.canvas.bind('<Enter>', self.on_enter)
        self.canvas.bind('<Leave>', self.on_leave)
        
        # 为灰色区域绑定事件
        self.upper_gray.bind('<Button-1>', self.start_drag)
        self.upper_gray.bind('<B1-Motion>', self.drag)
        self.upper_gray.bind('<Button-2>', self.show_menu)  # Mac上右键是Button-2
        self.upper_gray.bind('<Double-Button-1>', self.show_menu)  # Mac上双指单击
        self.upper_gray.bind('<Control-Button-1>', self.show_menu)  # Mac上Control+单指单击
        
        self.lower_gray.bind('<Button-1>', self.start_drag)
        self.lower_gray.bind('<B1-Motion>', self.drag)
        self.lower_gray.bind('<Button-2>', self.show_menu)  # Mac上右键是Button-2
        self.lower_gray.bind('<Double-Button-1>', self.show_menu)  # Mac上双指单击
        self.lower_gray.bind('<Control-Button-1>', self.show_menu)  # Mac上Control+单指单击
        
        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0, bg='#F0F0F0', fg='#333333', 
                           activebackground='#4A90E2', activeforeground='white',
                           relief='flat', borderwidth=1)
        self.menu.add_command(label=f"  {self.get_text('split')}  ", command=self.split_screen)
        self.menu.add_command(label=f"  {self.get_text('restore')}  ", command=self.restore_screen)
        self.menu.add_separator()
        
        # 颜色子菜单
        self.color_menu = tk.Menu(self.menu, tearoff=0, bg='#F0F0F0', fg='#333333',
                                 activebackground='#4A90E2', activeforeground='white',
                                 relief='flat', borderwidth=1)
        self.menu.add_cascade(label=f"  {self.get_text('select_color')}  ", menu=self.color_menu)
        self.color_menu.add_command(label=f"  {self.get_text('blue')}  ", command=lambda: self.change_color("blue"))
        self.color_menu.add_command(label=f"  {self.get_text('red')}  ", command=lambda: self.change_color("red"))
        self.color_menu.add_command(label=f"  {self.get_text('yellow')}  ", command=lambda: self.change_color("yellow"))
        self.color_menu.add_command(label=f"  {self.get_text('gray')}  ", command=lambda: self.change_color("gray"))
        self.color_menu.add_command(label=f"  {self.get_text('white')}  ", command=lambda: self.change_color("white"))
        self.color_menu.add_command(label=f"  {self.get_text('black')}  ", command=lambda: self.change_color("black"))
        
        # 分割模式子菜单
        self.split_mode_menu = tk.Menu(self.menu, tearoff=0, bg='#F0F0F0', fg='#333333',
                                      activebackground='#4A90E2', activeforeground='white',
                                      relief='flat', borderwidth=1)
        self.menu.add_cascade(label=f"  {self.get_text('split_mode')}  ", menu=self.split_mode_menu)
        self.split_mode_menu.add_command(label=f"  {self.get_text('fix_upper')}  ", command=lambda: self.change_split_mode("upper"))
        self.split_mode_menu.add_command(label=f"  {self.get_text('fix_lower')}  ", command=lambda: self.change_split_mode("lower"))
        
        # 语言子菜单
        self.language_menu = tk.Menu(self.menu, tearoff=0, bg='#F0F0F0', fg='#333333',
                                    activebackground='#4A90E2', activeforeground='white',
                                    relief='flat', borderwidth=1)
        self.menu.add_cascade(label=f"  {self.get_text('language')}  ", menu=self.language_menu)
        self.language_menu.add_command(label=f"  {self.get_text('chinese')}  ", command=lambda: self.change_language("zh"))
        self.language_menu.add_command(label=f"  {self.get_text('english')}  ", command=lambda: self.change_language("en"))
        
        self.menu.add_separator()
        self.menu.add_command(label=f"  {self.get_text('close')}  ", command=self.quit_app)
        
        # 启动定时器，定期检查横杠可见性
        self.check_visibility()
        
        # 启动窗口
        self.root.mainloop()
    
    def load_settings(self):
        """加载所有设置"""
        try:
            # 尝试从临时目录加载配置
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_config_file = os.path.join(temp_dir, "screen_divider_config.json")
            if os.path.exists(temp_config_file):
                with open(temp_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return {
                        'language': config.get('language', 'zh'),
                        'split_mode': config.get('split_mode', 'upper'),
                        'color': config.get('color', 'gray')
                    }
        except:
            pass
        
        # 如果无法从临时文件加载，使用默认设置
        return {
            'language': 'zh',  # 默认中文
            'split_mode': 'upper',  # 默认上方分割
            'color': 'gray'  # 默认灰色
        }
    
    def save_settings(self):
        """保存所有设置到临时文件"""
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_config_file = os.path.join(temp_dir, "screen_divider_config.json")
            config = {
                'language': self.current_language,
                'split_mode': self.split_mode,
                'color': self.current_color
            }
            with open(temp_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def get_text(self, key):
        """获取当前语言的文本"""
        return self.languages[self.current_language].get(key, key)
    
    def draw_line(self):
        """绘制横杠效果"""
        # 清除画布
        self.canvas.delete("all")
        
        # 获取当前颜色的渐变配置
        gradient = self.colors[self.current_color]["gradient"]
        
        # 绘制渐变效果
        for i in range(6):
            r = int(gradient[0][0] + (gradient[1][0] - gradient[0][0]) * i / 5)
            g = int(gradient[0][1] + (gradient[1][1] - gradient[0][1]) * i / 5)
            b = int(gradient[0][2] + (gradient[1][2] - gradient[0][2]) * i / 5)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, self.screen_width, i, 
                                  fill=color, width=1)
    
    def on_enter(self, event):
        """鼠标进入"""
        self.is_hovered = True
        self.canvas.configure(bg=self.colors[self.current_color]["hover"])
        self.draw_line()
    
    def on_leave(self, event):
        """鼠标离开"""
        self.is_hovered = False
        self.canvas.configure(bg=self.colors[self.current_color]["normal"])
        self.draw_line()
    
    def start_drag(self, event):
        """开始拖动"""
        self.drag_start_y = event.y_root
        self.canvas.configure(cursor="hand2")
    
    def drag(self, event):
        """拖动横杠"""
        if hasattr(self, 'drag_start_y'):
            delta_y = event.y_root - self.drag_start_y
            current_y = self.root.winfo_y()
            new_y = max(0, min(self.screen_height - 20, current_y + delta_y))  # 20像素高度
            # 保持窗口宽度为屏幕宽度，高度为20像素
            self.root.geometry(f"{self.screen_width}x20+0+{new_y}")
            self.drag_start_y = event.y_root
    
    def show_menu(self, event):
        """显示右键菜单"""
        self.menu.post(event.x_root, event.y_root)
    
    def change_color(self, color_name):
        """切换颜色"""
        if color_name in self.colors:
            self.current_color = color_name
            self.canvas.configure(bg=self.colors[color_name]["normal"])
            self.draw_line()
            self.save_settings()  # 保存设置
            print(f"颜色已切换为: {color_name}")
    
    def change_language(self, language_code):
        """切换语言"""
        if language_code in self.languages:
            self.current_language = language_code
            self.update_menu_texts()
            self.save_settings()  # 保存设置
            print(f"语言已切换为: {language_code}")
    
    def change_split_mode(self, mode):
        """切换分割模式"""
        self.split_mode = mode
        self.save_settings()  # 保存设置
        print(f"分割模式已切换为: {mode}")
        # 如果当前正在分割状态，需要重新分割以应用新模式
        if self.is_splitting:
            self.restore_screen()
            # 短暂延迟后重新分割
            self.root.after(100, self.split_screen)
    
    def update_menu_texts(self):
        """更新菜单文本"""
        try:
            # 重新创建菜单以更新所有文本
            self.menu.delete(0, tk.END)
            
            # 重新添加主菜单项
            self.menu.add_command(label=f"  {self.get_text('split')}  ", command=self.split_screen)
            self.menu.add_command(label=f"  {self.get_text('restore')}  ", command=self.restore_screen)
            self.menu.add_separator()
            
            # 重新创建颜色子菜单
            self.color_menu.delete(0, tk.END)
            self.menu.add_cascade(label=f"  {self.get_text('select_color')}  ", menu=self.color_menu)
            self.color_menu.add_command(label=f"  {self.get_text('blue')}  ", command=lambda: self.change_color("blue"))
            self.color_menu.add_command(label=f"  {self.get_text('red')}  ", command=lambda: self.change_color("red"))
            self.color_menu.add_command(label=f"  {self.get_text('yellow')}  ", command=lambda: self.change_color("yellow"))
            self.color_menu.add_command(label=f"  {self.get_text('gray')}  ", command=lambda: self.change_color("gray"))
            self.color_menu.add_command(label=f"  {self.get_text('white')}  ", command=lambda: self.change_color("white"))
            self.color_menu.add_command(label=f"  {self.get_text('black')}  ", command=lambda: self.change_color("black"))
            
            # 重新创建分割模式子菜单
            self.split_mode_menu.delete(0, tk.END)
            self.menu.add_cascade(label=f"  {self.get_text('split_mode')}  ", menu=self.split_mode_menu)
            self.split_mode_menu.add_command(label=f"  {self.get_text('fix_upper')}  ", command=lambda: self.change_split_mode("upper"))
            self.split_mode_menu.add_command(label=f"  {self.get_text('fix_lower')}  ", command=lambda: self.change_split_mode("lower"))
            
            # 重新创建语言子菜单
            self.language_menu.delete(0, tk.END)
            self.menu.add_cascade(label=f"  {self.get_text('language')}  ", menu=self.language_menu)
            self.language_menu.add_command(label=f"  {self.get_text('chinese')}  ", command=lambda: self.change_language("zh"))
            self.language_menu.add_command(label=f"  {self.get_text('english')}  ", command=lambda: self.change_language("en"))
            
            self.menu.add_separator()
            self.menu.add_command(label=f"  {self.get_text('close')}  ", command=self.quit_app)
            
        except Exception as e:
            print(f"更新菜单文本时发生错误: {e}")
    
    def on_focus_out(self, event):
        """窗口失去焦点时立即重新置顶和获得焦点"""
        if not self.is_splitting:  # 只在非分割状态下保持焦点
            self.root.after(50, self.ensure_topmost)
    
    def on_map(self, event):
        """窗口显示时确保置顶"""
        self.ensure_topmost()
    
    def ensure_topmost(self):
        """确保横杠窗口始终置顶"""
        # 无论是否分割，横杠都应该保持可见
        self.root.lift()
        
        # Mac特殊设置：使用最高的窗口层级
        try:
            self.root.attributes('-type', 'utility')  # 工具窗口类型
            self.root.attributes('-topmost', True)
            self.root.wm_attributes('-topmost', 1)  # 强制置顶
            self.root.attributes('-level', 'floating')  # 系统级浮动窗口
            self.root.attributes('-modified', False)  # 始终可见
        except:
            self.root.attributes('-topmost', True)
        
        if not self.is_splitting:  # 只在非分割状态下获得焦点
            self.root.focus_force()
            # 强制更新窗口状态
            self.root.update()
    
    def check_visibility(self):
        """定期检查横杠可见性"""
        if not self.is_splitting:
            # 确保横杠始终可见和可操作
            self.root.lift()
            
            # Mac特殊设置：使用最高的窗口层级
            try:
                self.root.attributes('-type', 'utility')  # 工具窗口类型
                self.root.attributes('-topmost', True)
                self.root.wm_attributes('-topmost', 1)  # 强制置顶
                self.root.attributes('-level', 'floating')  # 系统级浮动窗口
                self.root.attributes('-modified', False)  # 始终可见
            except:
                self.root.attributes('-topmost', True)
            
            # 每500ms检查一次
            self.root.after(500, self.check_visibility)
        else:
            # 分割状态下，只保持置顶但不强制焦点
            self.root.lift()
            
            # Mac特殊设置：使用最高的窗口层级
            try:
                self.root.attributes('-type', 'utility')  # 工具窗口类型
                self.root.attributes('-topmost', True)
                self.root.wm_attributes('-topmost', 1)  # 强制置顶
                self.root.attributes('-level', 'floating')  # 系统级浮动窗口
                self.root.attributes('-modified', False)  # 始终可见
            except:
                self.root.attributes('-topmost', True)
            
            # 分割状态下也定期检查
            self.root.after(1000, self.check_visibility)
    
    def check_screen_recording_permission(self):
        """检查屏幕录制权限"""
        try:
            # 尝试截取一个小区域来测试权限
            test_screenshot = ImageGrab.grab(bbox=(0, 0, 1, 1))
            # 如果截图成功且不是纯黑色，说明有权限
            if test_screenshot and test_screenshot.getpixel((0, 0)) != (0, 0, 0):
                return True
            else:
                return False
        except Exception as e:
            print(f"权限检查失败: {e}")
            return False
    
    def show_permission_dialog(self):
        """显示权限提示对话框"""
        if self.current_language == 'zh':
            title = "需要屏幕录制权限"
            message = "此应用需要屏幕录制权限才能正常工作。\n\n请按以下步骤操作：\n1. 打开 系统偏好设置 > 安全性与隐私 > 隐私\n2. 选择 屏幕录制\n3. 勾选 ScreenDivider\n4. 重启应用\n\n是否现在打开系统偏好设置？"
        else:
            title = "Screen Recording Permission Required"
            message = "This app requires screen recording permission to function properly.\n\nPlease follow these steps:\n1. Open System Preferences > Security & Privacy > Privacy\n2. Select Screen Recording\n3. Check ScreenDivider\n4. Restart the app\n\nOpen System Preferences now?"
        
        result = messagebox.askyesno(title, message)
        if result:
            try:
                import subprocess
                subprocess.run(["open", "-b", "com.apple.preference.security"])
            except Exception as e:
                print(f"无法打开系统偏好设置: {e}")
    
    def capture_upper_screen(self):
        """捕获上半部分屏幕"""
        try:
            # 检查屏幕录制权限
            if not self.check_screen_recording_permission():
                self.show_permission_dialog()
                return None
            
            # 获取横杠的真实屏幕位置（窗口Y坐标 + 窗口高度）
            window_y = self.root.winfo_y()
            window_height = self.root.winfo_height()
            split_y = window_y + window_height
            
            # Mac状态栏高度通常为25-28像素，为避免重复显示，从状态栏下方开始截图
            status_bar_height = 28
            start_y = status_bar_height
            
            # 确保坐标有效
            if split_y <= start_y:
                split_y = start_y + 1
            if split_y >= self.screen_height:
                split_y = self.screen_height - 1
            
            # 等待窗口完全定位
            self.root.update()
            time.sleep(0.3)  # 增加等待时间，确保右键菜单残影消失
            
            # 捕获横杠上方的屏幕区域（排除状态栏）
            bbox = (0, start_y, self.screen_width, split_y)
            print(f"截图区域: {bbox}, 屏幕尺寸: {self.screen_width}x{self.screen_height}")
            print(f"窗口位置: ({self.root.winfo_x()}, {window_y}), 窗口大小: {self.root.winfo_width()}x{window_height}")
            print(f"横杠真实Y位置: {split_y}, 排除状态栏高度: {status_bar_height}")
            
            # 尝试截图 - Mac版本使用ImageGrab
            screenshot = ImageGrab.grab(bbox=bbox)
            print(f"截图尺寸: {screenshot.size}")
            
            return screenshot
        except Exception as e:
            print(f"截图失败: {e}")
            return None
    
    def capture_lower_screen(self):
        """捕获下半部分屏幕"""
        try:
            # 检查屏幕录制权限
            if not self.check_screen_recording_permission():
                self.show_permission_dialog()
                return None
            
            # 获取横杠的真实屏幕位置（窗口Y坐标）
            window_y = self.root.winfo_y()
            start_y = window_y
            
            # 确保坐标有效
            if start_y <= 0:
                start_y = 1
            if start_y >= self.screen_height:
                start_y = self.screen_height - 1
            
            # 等待窗口完全定位
            self.root.update()
            time.sleep(0.3)  # 增加等待时间，确保右键菜单残影消失
            
            # 捕获横杠下方的屏幕区域
            bbox = (0, start_y, self.screen_width, self.screen_height)
            print(f"下方截图区域: {bbox}, 屏幕尺寸: {self.screen_width}x{self.screen_height}")
            print(f"窗口位置: ({self.root.winfo_x()}, {window_y})")
            print(f"横杠Y位置: {start_y}")
            
            # 尝试截图 - Mac版本使用ImageGrab
            screenshot = ImageGrab.grab(bbox=bbox)
            print(f"下方截图尺寸: {screenshot.size}")
            
            return screenshot
        except Exception as e:
            print(f"下方截图失败: {e}")
            return None
    
    def split_screen(self):
        """分割屏幕"""
        if not self.is_splitting:
            try:
                self.is_splitting = True
                
                # 根据分割模式捕获相应部分屏幕
                if self.split_mode == "upper":
                    self.fixed_image = self.capture_upper_screen()
                    print(f"使用上方分割模式")
                else:  # lower
                    self.fixed_image = self.capture_lower_screen()
                    print(f"使用下方分割模式")
                    
                if self.fixed_image is None:
                    messagebox.showerror("错误", self.get_text("error_capture"))
                    self.is_splitting = False
                    return
                
                # 获取截图的高度
                split_height = self.fixed_image.size[1]
                
                # 根据分割模式确定窗口位置
                if self.split_mode == "upper":
                    # Mac状态栏高度，固定窗口应该从状态栏下方开始
                    status_bar_height = 28
                    window_y = status_bar_height
                    print(f"创建上方固定窗口")
                else:  # lower
                    # 下方模式：窗口从横杠位置开始到屏幕底部
                    window_y = self.root.winfo_y()
                    print(f"创建下方固定窗口")
                
                # 创建固定窗口
                self.upper_window = tk.Toplevel()
                self.upper_window.geometry(f"{self.screen_width}x{split_height}+0+{window_y}")
                self.upper_window.overrideredirect(True)
                
                # Mac特殊设置：使用最高窗口层级，确保在全屏应用上方显示
                try:
                    self.upper_window.attributes('-type', 'utility')  # 工具窗口类型
                    self.upper_window.attributes('-topmost', True)
                    self.upper_window.wm_attributes('-topmost', 1)  # 强制置顶
                    # 尝试设置为系统级窗口
                    self.upper_window.attributes('-level', 'floating')
                except:
                    self.upper_window.attributes('-topmost', True)
                
                self.upper_window.attributes('-alpha', 1.0)  # 完全不透明
                self.upper_window.resizable(False, False)  # 禁止调整大小
                print(f"创建固定窗口，尺寸: {self.screen_width}x{split_height}, 位置: +0+{window_y}, 模式: {self.split_mode}")
                
                # 等待窗口完全创建
                self.upper_window.update_idletasks()
                self.upper_window.update()
                time.sleep(0.1)  # 短暂等待确保窗口稳定
                
                # 创建画布显示固定图像
                print(f"创建画布，窗口尺寸: {self.screen_width}x{split_height}")
                self.upper_canvas = tk.Canvas(self.upper_window, 
                                            width=self.screen_width, 
                                            height=split_height,
                                            highlightthickness=0)
                self.upper_canvas.pack(fill='both', expand=True)
                
                # 等待画布完全创建
                self.upper_window.update_idletasks()
                self.upper_window.update()
                time.sleep(0.1)
                print(f"画布创建完成，实际尺寸: {self.upper_canvas.winfo_width()}x{self.upper_canvas.winfo_height()}")
                
                # 显示固定图像
                print(f"准备显示图像，尺寸: {self.fixed_image.size}")
                self.photo = ImageTk.PhotoImage(self.fixed_image)
                print(f"PhotoImage创建成功，尺寸: {self.photo.width()}x{self.photo.height()}")
                
                # 在画布中心显示图像
                canvas_width = self.upper_canvas.winfo_width()
                canvas_height = self.upper_canvas.winfo_height()
                image_width = self.photo.width()
                image_height = self.photo.height()
                
                # 计算图像在画布中的位置（左上角对齐）
                x = 0
                y = 0
                
                print(f"画布尺寸: {canvas_width}x{canvas_height}, 图像尺寸: {image_width}x{image_height}")
                print(f"图像位置: ({x}, {y})")
                
                self.upper_canvas.create_image(x, y, anchor='nw', image=self.photo)
                print(f"图像已添加到画布")
                
                # 再次强制更新
                self.upper_window.update()
                
                # 绑定滚轮事件到上半部分 - Mac滚轮事件
                self.upper_canvas.bind('<MouseWheel>', self.block_scroll)  # Mac滚轮
                self.upper_canvas.bind('<Button-4>', self.block_scroll)  # Linux滚轮上
                self.upper_canvas.bind('<Button-5>', self.block_scroll)  # Linux滚轮下
                
                # 绑定鼠标事件，确保优先级 - Mac鼠标按钮
                self.upper_canvas.bind('<Button-1>', self.block_all)  # 左键
                self.upper_canvas.bind('<Button-2>', self.block_all)  # 右键
                self.upper_canvas.bind('<Button-3>', self.block_all)  # 中键
                self.upper_canvas.bind('<Motion>', self.block_all)  # 移动
                
                # 使上半部分窗口获得焦点并置顶
                self.upper_window.focus_force()
                self.upper_window.lift()
                self.upper_window.attributes('-topmost', True)
                
                # 分割状态下，横杠仍然保持置顶但优先级较低
                # 不取消横杠的置顶状态，让它保持可见
                
                # 更新菜单状态
                self.menu.entryconfig(0, state="disabled")  # 分割屏幕
                self.menu.entryconfig(1, state="normal")    # 恢复屏幕
                
            except Exception as e:
                messagebox.showerror("错误", f"{self.get_text('error_split')}{str(e)}")
    
    def block_scroll(self, event):
        """阻止滚轮事件"""
        return "break"
    
    def block_all(self, event):
        """阻止所有鼠标事件"""
        return "break"
    
    def restore_screen(self):
        """恢复屏幕"""
        if self.is_splitting:
            try:
                print("开始恢复屏幕...")
                self.is_splitting = False
                
                # 销毁固定窗口
                if self.upper_window:
                    print("销毁固定窗口...")
                    self.upper_window.destroy()
                    self.upper_window = None
                
                # 清理图像资源
                if hasattr(self, 'photo'):
                    print("清理图像资源...")
                    delattr(self, 'photo')
                if hasattr(self, 'upper_canvas'):
                    delattr(self, 'upper_canvas')
                self.fixed_image = None
                
                # 恢复横杠的焦点状态
                self.root.focus_force()
                
                # 更新菜单状态
                self.menu.entryconfig(0, state="normal")    # 分割屏幕
                self.menu.entryconfig(1, state="disabled")  # 恢复屏幕
                
                print("屏幕恢复完成")
            except Exception as e:
                print(f"恢复屏幕时发生错误：{str(e)}")
                messagebox.showerror("错误", f"{self.get_text('error_restore')}{str(e)}")
    
    def quit_app(self):
        """关闭软件"""
        try:
            if self.is_splitting:
                self.restore_screen()
            self.root.quit()
        except:
            sys.exit(0)

def main():
    try:
        app = ScreenDivider()
    except Exception as e:
        # 这里不能使用app.get_text，因为app可能还没有创建成功
        messagebox.showerror("启动错误", f"程序启动失败：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()