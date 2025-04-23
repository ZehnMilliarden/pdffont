import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import sys

# 导入字体提取器类
from pdf_font_extractor import PdfFontExtractor

class PdfFontApp:
    """PDF字体提取和预览应用程序"""
    
    def __init__(self, root=None):
        """初始化应用程序界面
        
        参数:
            root: tkinter根窗口，如果为None则创建新窗口
        """
        # 创建主窗口
        if root is None:
            self.root = tk.Tk()
        else:
            self.root = root
            
        self.root.title("PDF字体提取和预览工具")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 创建字体提取器
        self.font_extractor = PdfFontExtractor()
        
        # 当前字体列表和选中的字体
        self.fonts = []
        self.current_font = None
        
        # 创建UI组件
        self._create_ui()
        
    def _create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="PDF文件选择")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 文件路径输入框和浏览按钮
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(file_select_frame, text="PDF文件:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_select_frame, textvariable=self.file_path_var, width=60)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(file_select_frame, text="浏览...", command=self._browse_file)
        browse_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        load_btn = ttk.Button(file_select_frame, text="加载字体", command=self._load_fonts)
        load_btn.pack(side=tk.LEFT)
        
        # 主内容区域 - 使用PanedWindow分割
        content_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧字体列表区域
        left_frame = ttk.LabelFrame(content_paned, text="可用字体")
        content_paned.add(left_frame, weight=1)
        
        # 字体列表框架
        font_list_frame = ttk.Frame(left_frame)
        font_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建字体列表和滚动条
        self.font_listbox = tk.Listbox(font_list_frame, width=30)
        self.font_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(font_list_frame, orient="vertical", command=self.font_listbox.yview)
        self.font_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定字体选择事件
        self.font_listbox.bind('<<ListboxSelect>>', self._on_font_select)
        
        # 右侧预览区域
        right_frame = ttk.Frame(content_paned)
        content_paned.add(right_frame, weight=3)
        
        # 预览设置区域
        settings_frame = ttk.LabelFrame(right_frame, text="预览设置")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 文本输入区域
        text_frame = ttk.Frame(settings_frame)
        text_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(text_frame, text="预览文本:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.text_var = tk.StringVar(value="Hello 你好！字体预览 1234567890")
        text_entry = ttk.Entry(text_frame, textvariable=self.text_var, width=50)
        text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 字体大小设置
        size_frame = ttk.Frame(settings_frame)
        size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(size_frame, text="字体大小:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.size_var = tk.IntVar(value=24)
        size_slider = ttk.Scale(size_frame, from_=8, to=72, variable=self.size_var, 
                               orient=tk.HORIZONTAL, length=200)
        size_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.size_label = ttk.Label(size_frame, text="24")
        self.size_label.pack(side=tk.LEFT, padx=5)
        
        # 更新按钮
        update_btn = ttk.Button(settings_frame, text="更新预览", command=self._update_preview)
        update_btn.pack(anchor=tk.E, padx=10, pady=5)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(right_frame, text="预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg="white")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 预览图像标签
        self.preview_label = ttk.Label(self.preview_canvas)
        self.preview_canvas.create_window(0, 0, anchor=tk.NW, window=self.preview_label)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪。请选择PDF文件")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定事件
        self.text_var.trace_add("write", lambda *args: self._update_preview())
        self.size_var.trace_add("write", lambda *args: self._update_size_label())
    
    def _browse_file(self):
        """打开文件选择对话框"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.status_var.set(f"已选择: {file_path}")
    
    def _load_fonts(self):
        """加载PDF文件中的字体"""
        pdf_path = self.file_path_var.get()
        
        if not pdf_path:
            self.status_var.set("错误: 请先选择PDF文件")
            return
            
        try:
            self.status_var.set(f"正在从 {pdf_path} 加载字体...")
            self.root.update()  # 强制更新UI
            
            # 清空字体列表
            self.font_listbox.delete(0, tk.END)
            self.fonts = []
            self.current_font = None
            
            # 打开PDF文件并提取字体
            self.font_extractor.open(pdf_path)
            self.fonts = self.font_extractor.extract_fonts()
            
            # 更新字体列表
            self.font_map = {}  # 字体名称到字体对象的映射
            for i, font in enumerate(self.fonts):
                font_name = font.get('family_name', font.get('basename', f"Font {i+1}"))
                self.font_listbox.insert(tk.END, font_name)
                self.font_map[font_name] = font
            
            # 默认选中第一个字体
            if self.fonts:
                self.font_listbox.selection_set(0)
                self.font_listbox.event_generate('<<ListboxSelect>>')
                self.status_var.set(f"已加载 {len(self.fonts)} 个字体")
            else:
                self.status_var.set("未找到可用字体")
            
        except Exception as e:
            self.status_var.set(f"错误: {str(e)}")
    
    def _on_font_select(self, event):
        """字体选择事件处理"""
        selection = self.font_listbox.curselection()
        if selection:
            font_name = self.font_listbox.get(selection[0])
            self.current_font = self.font_map.get(font_name)
            self._update_preview()
    
    def _update_size_label(self):
        """更新字体大小标签"""
        size = self.size_var.get()
        self.size_label.config(text=str(size))
        self._update_preview()
    
    def _update_preview(self):
        """更新字体预览"""
        if not self.current_font:
            return
            
        # 获取当前设置
        preview_text = self.text_var.get()
        font_size = self.size_var.get()
        
        # 渲染预览
        buffer = self.current_font.get('buffer')
        if buffer:
            img = self.font_extractor.render_text_with_font(buffer, preview_text, font_size)
            if img:
                # 转换为Tkinter图像并显示
                self.tk_img = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=self.tk_img)
                
                # 调整画布大小
                self.preview_canvas.config(width=img.width, height=img.height)
                self.preview_canvas.create_window(img.width//2, img.height//2, window=self.preview_label)
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()


if __name__ == "__main__":
    try:
        # 检查是否安装了必要的库
        import fontTools
        from PIL import Image, ImageDraw, ImageFont
        
        # 启动应用程序
        app = PdfFontApp()
        app.run()
        
    except ImportError as e:
        print(f"缺少必要的库: {e}")
        print("请安装必要的库: pip install fonttools pillow")
    except Exception as e:
        print(f"运行时错误: {e}")
