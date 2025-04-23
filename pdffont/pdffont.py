
import fitz
import io

class PdfFont:
    def __init__(self, path: str):
        self.__path__ = path
        self.__docs__ = fitz.open(path)
        self.__fonts__ = []

    def __del__(self):
        self.__docs__.close()

    def extract_fonts(self):
        """提取PDF中的所有字体，并返回字体对象列表"""
        font_objects = []
        unique_fonts = set()  # 用于跟踪已处理的字体，避免重复
        
        for page in self.__docs__:
            fonts = page.get_fonts()
            for font in fonts:
                self.__fonts__.append(font)

        for font in self.__fonts__:
            # 内嵌字体引用
            if font[0] == 0:
                font_name = font[3]
                if font_name not in unique_fonts:
                    print(f"内嵌字体名称: {font_name}")
                    unique_fonts.add(font_name)
                continue
            
            # 提取字体数据
            basename, ext, _, buffer = self.__docs__.extract_font(font[0])
            font_key = f"{basename}.{ext}"
            
            # 避免重复处理相同的字体
            if font_key in unique_fonts:
                continue
                
            unique_fonts.add(font_key)
            print(f"提取字体: {font_key}")
            
            # 在内存中处理字体
            font_obj = self.process_font_in_memory(buffer, basename, ext)
            if font_obj:
                font_objects.append(font_obj)
                print(f"字体信息: {font_obj.get('family_name', 'Unknown')}")
            
        return font_objects
        
    def preview_fonts(self):
        """显示一个字体选择和预览窗口"""
        # 提取所有字体
        fonts = self.extract_fonts()
        
        if not fonts:
            print("没有找到可用的字体")
            return
            
        # 显示字体选择和预览窗口
        self.show_font_preview_window(fonts)

    def process_font_in_memory(self, buffer, basename, ext):
        """在内存中处理字体数据"""
        try:
            # 使用fontTools库处理字体
            from fontTools.ttLib import TTFont
            
            # 创建内存文件对象
            font_stream = io.BytesIO(buffer)
            
            # 从内存加载字体
            font = TTFont(font_stream)
            
            # 获取字体名称信息
            name_records = font["name"].names
            family_name = None
            full_name = None
            
            for record in name_records:
                if record.nameID == 1 and not family_name:  # Family name
                    if record.isUnicode():
                        family_name = record.string.decode("utf-16-be")
                    else:
                        family_name = record.string.decode("latin1")
                
                if record.nameID == 4 and not full_name:  # Full name
                    if record.isUnicode():
                        full_name = record.string.decode("utf-16-be")
                    else:
                        full_name = record.string.decode("latin1")
            
            # 获取支持的字符集
            cmap = font.getBestCmap()
            supported_chars = list(cmap.keys()) if cmap else []
            
            # 返回字体对象和相关信息
            return {
                "font_obj": font,
                "buffer": buffer,
                "basename": basename,
                "ext": ext,
                "family_name": family_name or "Unknown",
                "full_name": full_name or basename,
                "num_glyphs": len(font.getGlyphOrder()),
                "tables": list(font.keys()),
                "supported_chars": supported_chars[:100] if supported_chars else []  # 只返回前100个支持的字符码点
            }
        except Exception as e:
            print(f"处理字体时出错: {e}")
            return None
        finally:
            if 'font_stream' in locals():
                font_stream.close()

    def render_text_with_font(self, buffer, text, size=24, font_color=(0, 0, 0), bg_color=(255, 255, 255)):
        """使用指定字体渲染文本并返回图像"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建内存中的字体对象
            font_stream = io.BytesIO(buffer)
            font = ImageFont.truetype(font_stream, size)
            
            # 计算文本尺寸以确定图像大小
            try:
                text_width, text_height = font.getsize(text)
            except AttributeError:
                # 新版Pillow使用getbbox或getlength
                try:
                    bbox = font.getbbox(text)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except AttributeError:
                    # 如果以上方法都不可用，使用默认尺寸
                    text_width = 300
                    text_height = 50
            
            # 添加边距
            img_width = text_width + 40
            img_height = text_height + 40
            
            # 创建图像并渲染文本
            img = Image.new("RGB", (img_width, img_height), color=bg_color)
            draw = ImageDraw.Draw(img)
            
            # 计算文本位置（居中）
            x = (img_width - text_width) // 2 if text_width < img_width else 10
            y = (img_height - text_height) // 2 if text_height < img_height else 10
            
            # 绘制文本
            draw.text((x, y), text, font=font, fill=font_color)
            font_stream.close()
            
            return img
        except Exception as e:
            print(f"渲染文本时出错: {e}")
            return None
    
    def show_font_preview_window(self, fonts):
        """显示字体选择和预览窗口，使用两栏布局"""
        try:
            import tkinter as tk
            from tkinter import ttk
            from PIL import ImageTk
            
            # 创建主窗口
            root = tk.Tk()
            root.title("PDF字体预览")
            root.geometry("900x600")
            root.minsize(800, 500)
            
            # 创建主要分割窗格，左右两栏
            main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
            main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 左侧字体列表框架
            left_frame = ttk.LabelFrame(main_paned, text="可用字体")
            main_paned.add(left_frame, weight=1)
            
            # 右侧预览框架
            right_frame = ttk.Frame(main_paned)
            main_paned.add(right_frame, weight=3)
            
            # 右侧上部设置区域
            settings_frame = ttk.LabelFrame(right_frame, text="预览设置")
            settings_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # 右侧下部预览区域
            preview_frame = ttk.LabelFrame(right_frame, text="预览")
            preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 创建字体列表
            font_listbox = tk.Listbox(left_frame, width=30, height=20)
            font_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(font_listbox, orient="vertical", command=font_listbox.yview)
            font_listbox.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 添加字体到列表
            font_map = {}  # 用于存储字体名称到字体对象的映射
            for i, font in enumerate(fonts):
                font_name = font.get('family_name', font.get('basename', f"Font {i+1}"))
                font_listbox.insert(tk.END, font_name)
                font_map[font_name] = font
            
            # 预览设置区域
            settings_inner_frame = ttk.Frame(settings_frame)
            settings_inner_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # 文本输入区域
            text_frame = ttk.Frame(settings_inner_frame)
            text_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(text_frame, text="预览文本:").pack(side=tk.LEFT, padx=5)
            text_var = tk.StringVar(value="Hello 你好！字体预览 1234567890")
            text_entry = ttk.Entry(text_frame, textvariable=text_var, width=50)
            text_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # 字体大小设置
            size_frame = ttk.Frame(settings_inner_frame)
            size_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(size_frame, text="字体大小:").pack(side=tk.LEFT, padx=5)
            size_var = tk.IntVar(value=24)
            
            # 大小滑块
            size_slider = ttk.Scale(size_frame, from_=8, to=72, variable=size_var, 
                                   orient=tk.HORIZONTAL, length=200)
            size_slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # 显示当前大小的标签
            size_label = ttk.Label(size_frame, text="24")
            size_label.pack(side=tk.LEFT, padx=5)
            
            # 预览图像标签
            preview_label = ttk.Label(preview_frame)
            preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 当前选中的字体
            current_font = None
            
            # 更新预览的函数
            def update_preview():
                if not current_font:
                    return
                    
                # 获取当前设置
                preview_text = text_var.get()
                font_size = size_var.get()
                size_label.config(text=str(font_size))  # 更新大小标签
                
                # 渲染预览
                buffer = current_font.get('buffer')
                if buffer:
                    img = self.render_text_with_font(buffer, preview_text, font_size)
                    if img:
                        # 转换为Tkinter图像并显示
                        tk_img = ImageTk.PhotoImage(img)
                        preview_label.configure(image=tk_img)
                        preview_label.image = tk_img  # 保持引用，防止垃圾回收
            
            # 字体选择事件
            def on_font_select(event):
                nonlocal current_font
                selection = font_listbox.curselection()
                if selection:
                    font_name = font_listbox.get(selection[0])
                    current_font = font_map.get(font_name)
                    update_preview()
            
            # 绑定选择事件
            font_listbox.bind('<<ListboxSelect>>', on_font_select)
            
            # 绑定文本和大小变化事件
            text_var.trace_add("write", lambda *args: update_preview())
            size_var.trace_add("write", lambda *args: update_preview())
            
            # 默认选中第一个字体
            if fonts:
                font_listbox.selection_set(0)
                font_listbox.event_generate('<<ListboxSelect>>')
            
            # 运行Tkinter主循环
            root.mainloop()
            
        except Exception as e:
            print(f"创建字体预览窗口时出错: {e}")
    
    def render_text_in_memory(self, buffer, text="Hello 你好！", size=24, font_color=(0, 0, 0), bg_color=(255, 255, 255)):
        """
        在内存中渲染文本并显示预览窗口（兼容旧版方法）
        """
        try:
            import tkinter as tk
            from tkinter import ttk
            from PIL import ImageTk, Image
            
            # 渲染文本
            img = self.render_text_with_font(buffer, text, size, font_color, bg_color)
            if not img:
                return None
                
            img_width, img_height = img.size
            
            # 创建主窗口
            root = tk.Tk()
            root.title("字体预览")
            root.geometry(f"{img_width+50}x{img_height+100}")
            
            # 创建图像标签
            tk_img = ImageTk.PhotoImage(img)
            img_label = ttk.Label(root, image=tk_img)
            img_label.pack(pady=10)
            img_label.image = tk_img  # 保持引用
            
            # 创建文本输入框
            text_var = tk.StringVar(value=text)
            text_entry = ttk.Entry(root, textvariable=text_var, width=30)
            text_entry.pack(pady=5)
            
            # 更新预览的函数
            def update_preview():
                new_text = text_var.get()
                # 渲染新文本
                new_img = self.render_text_with_font(buffer, new_text, size, font_color, bg_color)
                if new_img:
                    new_width, new_height = new_img.size
                    # 更新图像
                    nonlocal tk_img
                    tk_img = ImageTk.PhotoImage(new_img)
                    img_label.configure(image=tk_img)
                    img_label.image = tk_img  # 保持引用
                    
                    # 调整窗口大小但保持位置
                    x, y = root.winfo_x(), root.winfo_y()
                    root.geometry(f"{new_width+50}x{new_height+100}+{x}+{y}")
            
            # 创建更新按钮
            update_btn = ttk.Button(root, text="更新预览", command=update_preview)
            update_btn.pack(pady=5)
            
            # 运行Tkinter主循环
            root.mainloop()
            
            return {
                "image": img,
                "width": img_width,
                "height": img_height
            }
        except Exception as e:
            print(f"渲染文本时出错: {e}")
            return None
        finally:
            if 'font_stream' in locals():
                font_stream.close()

    
class PdfFontApp:
    """字体提取应用程序类"""
    def __init__(self):
        import tkinter as tk
        from tkinter import ttk, filedialog
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("PDF字体提取器")
        self.root.geometry("600x300")
        self.root.minsize(500, 250)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="PDF字体提取器", font=("Arial", 16))
        title_label.pack(pady=10)
        
        # 文件选择框架
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=10)
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="浏览...", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)
        
        # 提示信息
        info_label = ttk.Label(main_frame, text="选择一个PDF文件来提取字体")
        info_label.pack(pady=10)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪。请选择PDF文件")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        extract_btn = ttk.Button(button_frame, text="提取字体", command=self.extract_fonts)
        extract_btn.pack(side=tk.LEFT, padx=10)
        
        exit_btn = ttk.Button(button_frame, text="退出", command=self.root.destroy)
        exit_btn.pack(side=tk.LEFT, padx=10)
    
    def browse_file(self):
        """打开文件选择对话框"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.status_var.set(f"已选择: {file_path}")
    
    def extract_fonts(self):
        """从选定的PDF文件中提取字体"""
        pdf_path = self.file_path_var.get()
        
        if not pdf_path:
            self.status_var.set("错误: 请先选择PDF文件")
            return
            
        try:
            self.status_var.set(f"正在从 {pdf_path} 加载字体...")
            self.root.update()  # 强制更新UI
            
            # 创建PDF字体对象并显示预览
            pdf_font = PdfFont(pdf_path)
            pdf_font.preview_fonts()
            
        except Exception as e:
            self.status_var.set(f"错误: {str(e)}")
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()


if __name__ == "__main__":
    try:
        # 检查是否安装了必要的库
        import fontTools
        from PIL import Image, ImageDraw, ImageFont
        import tkinter as tk
        from tkinter import filedialog
        
        # 启动应用程序
        app = PdfFontApp()
        app.run()
        
    except ImportError as e:
        print(f"缺少必要的库: {e}")
        print("请安装必要的库: pip install fonttools pillow")
    except Exception as e:
        print(f"运行时错误: {e}")