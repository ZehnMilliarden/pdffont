import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import sys
import json
import re

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
        
        # 创建一个垂直分割的PanedWindow来分割预览区域和度量信息区域
        right_paned = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        right_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 预览区域（上部）
        preview_frame = ttk.LabelFrame(right_paned, text="预览")
        right_paned.add(preview_frame, weight=2)  # 设置权重为2
        
        # 创建预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg="white", height=200)  # 限制高度
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 预览图像标签
        self.preview_label = ttk.Label(self.preview_canvas)
        self.preview_canvas.create_window(0, 0, anchor=tk.NW, window=self.preview_label)
        
        # 字体度量信息区域（下部）
        metrics_frame = ttk.LabelFrame(right_paned, text="字体度量信息")
        right_paned.add(metrics_frame, weight=3)  # 设置权重为3，比预览区域大
        
        # 创建选项卡控件用于切换不同类型的字体信息
        metrics_notebook = ttk.Notebook(metrics_frame)
        metrics_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 选项卡一: 字体文件度量信息
        font_metrics_tab = ttk.Frame(metrics_notebook)
        metrics_notebook.add(font_metrics_tab, text="字体文件信息")
        
        # 创建文本区域显示字体文件度量信息
        self.metrics_text = tk.Text(font_metrics_tab, height=15, wrap=tk.WORD, font=("Consolas", 10))
        self.metrics_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 选项卡二: PDF原始字体描述符信息
        pdf_desc_tab = ttk.Frame(metrics_notebook)
        metrics_notebook.add(pdf_desc_tab, text="PDF字体描述符")
        
        # 创建树形视图显示原始字体描述符信息
        self.desc_tree = ttk.Treeview(pdf_desc_tab, columns=("value"), show="tree")
        
        # 设置树形视图的列宽度
        self.desc_tree.column("#0", width=400, stretch=tk.YES)  # 第一列（树形结构列）
        
        # 创建水平滚动条
        desc_h_scrollbar = ttk.Scrollbar(pdf_desc_tab, orient="horizontal", command=self.desc_tree.xview)
        self.desc_tree.configure(xscrollcommand=desc_h_scrollbar.set)
        desc_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 添加垂直滚动条
        desc_v_scrollbar = ttk.Scrollbar(pdf_desc_tab, orient="vertical", command=self.desc_tree.yview)
        self.desc_tree.configure(yscrollcommand=desc_v_scrollbar.set)
        desc_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建右键菜单
        self.desc_tree_menu = tk.Menu(self.desc_tree, tearoff=0)
        self.desc_tree_menu.add_command(label="复制", command=self._copy_as_json)
        
        # 绑定右键菜单
        self.desc_tree.bind("<Button-3>", self._show_context_menu)
        
        # 存储当前选中的项目
        self.selected_item = None
        self.desc_tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # 在添加滚动条后再打包树形视图
        self.desc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加滚动条
        metrics_scrollbar = ttk.Scrollbar(self.metrics_text, orient="vertical", command=self.metrics_text.yview)
        self.metrics_text.configure(yscrollcommand=metrics_scrollbar.set)
        metrics_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 设置为只读
        self.metrics_text.config(state=tk.DISABLED)
        
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
            
            # 清空字体描述符树形视图
            self.desc_tree.delete(*self.desc_tree.get_children())
            
            # 打开PDF文件并提取字体
            self.font_extractor.open(pdf_path)
            self.fonts = self.font_extractor.extract_fonts()
            
            # 提取PDF原始字体描述符信息
            self.status_var.set(f"正在提取PDF字体描述符信息...")
            self.root.update()  # 强制更新UI
            self.font_descriptors = self.font_extractor.extract_font_descriptors()
            
            # 更新字体列表
            self.font_map = {}  # 字体名称到字体对象的映射
            self.desc_map = {}  # 字体名称到字体描述符的映射
            
            # 处理字体文件信息
            for i, font in enumerate(self.fonts):
                font_name = font.get('family_name', font.get('basename', f"Font {i+1}"))
                self.font_listbox.insert(tk.END, font_name)
                self.font_map[font_name] = font
            
            # 建立字体名称到字体描述符的映射
            for desc in self.font_descriptors:
                desc_name = desc.get('name', '')
                # 尝试匹配字体名称
                for font_name in self.font_map.keys():
                    # 如果字体名称包含在描述符名称中，或者描述符名称包含在字体名称中
                    if desc_name in font_name or font_name in desc_name:
                        self.desc_map[font_name] = desc
                        break
            
            # 默认选中第一个字体
            if self.fonts:
                self.font_listbox.selection_set(0)
                self.font_listbox.event_generate('<<ListboxSelect>>')
                self.status_var.set(f"已加载 {len(self.fonts)} 个字体和 {len(self.font_descriptors)} 个字体描述符")
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
            self._update_font_descriptor(font_name)
    
    def _update_size_label(self):
        """更新字体大小标签"""
        size = self.size_var.get()
        self.size_label.config(text=str(size))
        self._update_preview()
    
    def _update_preview(self):
        """更新字体预览和度量信息"""
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
        
        # 更新字体度量信息
        self._update_metrics_info()
    
    def _update_metrics_info(self):
        """更新字体度量信息显示"""
        # 清空度量信息区域
        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete(1.0, tk.END)
        
        if not self.current_font:
            self.metrics_text.config(state=tk.DISABLED)
            return
        
        # 获取字体度量信息
        metrics = self.current_font.get('metrics', {})
        if not metrics:
            self.metrics_text.insert(tk.END, "无可用的字体度量信息")
            self.metrics_text.config(state=tk.DISABLED)
            return
        
        # 添加基本信息
        self.metrics_text.insert(tk.END, f"字体名称: {self.current_font.get('family_name', '未知')}\n")
        self.metrics_text.insert(tk.END, f"字体全名: {self.current_font.get('full_name', '未知')}\n")
        self.metrics_text.insert(tk.END, f"字形数量: {self.current_font.get('num_glyphs', 0)}\n\n")
        
        # 添加度量信息
        self.metrics_text.insert(tk.END, "字体度量信息:\n")
        
        # 添加单位信息
        if "units_per_em" in metrics:
            self.metrics_text.insert(tk.END, f"  每 EM 单位数: {metrics['units_per_em']}\n")
        
        # 添加边界框信息
        if all(k in metrics for k in ["x_min", "y_min", "x_max", "y_max"]):
            self.metrics_text.insert(tk.END, f"  边界框: ({metrics['x_min']}, {metrics['y_min']}) - ({metrics['x_max']}, {metrics['y_max']})\n")
        
        # 添加上升、下降和行间距信息
        if all(k in metrics for k in ["ascent", "descent", "line_gap"]):
            self.metrics_text.insert(tk.END, f"  上升部分: {metrics['ascent']}\n")
            self.metrics_text.insert(tk.END, f"  下降部分: {metrics['descent']}\n")
            self.metrics_text.insert(tk.END, f"  行间距: {metrics['line_gap']}\n")
        
        # 添加字体类型信息
        if "weight_class" in metrics:
            weight_names = {
                100: "极细",
                200: "特细",
                300: "细",
                400: "标准",
                500: "中等",
                600: "半粗",
                700: "粗",
                800: "特粗",
                900: "极粗"
            }
            weight = metrics["weight_class"]
            weight_name = weight_names.get(weight, str(weight))
            self.metrics_text.insert(tk.END, f"  字重: {weight} ({weight_name})\n")
        
        if "width_class" in metrics:
            width_names = {
                1: "极窄",
                2: "特窄",
                3: "窄",
                4: "半窄",
                5: "中等",
                6: "半宽",
                7: "宽",
                8: "特宽",
                9: "极宽"
            }
            width = metrics["width_class"]
            width_name = width_names.get(width, str(width))
            self.metrics_text.insert(tk.END, f"  字宽: {width} ({width_name})\n")
        
        # 添加Panose信息
        if "panose" in metrics:
            panose = metrics["panose"]
            if panose:  # 确保panose字典不为空
                self.metrics_text.insert(tk.END, "\nPanose 信息:\n")
                
                # 字体族类型
                family_types = {
                    0: "任意",
                    1: "无衡线体",
                    2: "有衡线体",
                    3: "手写体",
                    4: "装饰体",
                    5: "脚本体"
                }
                
                family_type = panose.get('family_type', 0)
                self.metrics_text.insert(tk.END, f"  字体类型: {family_types.get(family_type, '未知')}\n")
                
                # 显示所有可用的Panose属性
                panose_names = {
                    'serif_style': '衡线风格',
                    'weight': '字重',
                    'proportion': '比例',
                    'contrast': '对比度',
                    'stroke_variation': '笔画变化',
                    'arm_style': '臂部风格',
                    'letterform': '字形',
                    'midline': '中线',
                    'x_height': 'x高度'
                }
                
                # 显示其他Panose属性（除了family_type之外）
                for attr, value in panose.items():
                    if attr != 'family_type' and attr in panose_names:
                        self.metrics_text.insert(tk.END, f"  {panose_names[attr]}: {value}\n")
        
        # 设置为只读
        self.metrics_text.config(state=tk.DISABLED)
    
    def _update_font_descriptor(self, font_name):
        """更新原始字体描述符信息显示"""
        # 清空树形视图
        self.desc_tree.delete(*self.desc_tree.get_children())
        
        # 获取字体描述符信息
        descriptor = self.desc_map.get(font_name)
        if not descriptor:
            self.desc_tree.insert("", "end", text=f"未找到 '{font_name}' 的原始字体描述符信息")
            return
        
        # 创建字体节点
        font_name_display = descriptor.get('name', '未知')
        font_node = self.desc_tree.insert("", "end", text=f"字体: {font_name_display}", open=True)
        
        # 添加基本信息
        basic_node = self.desc_tree.insert(font_node, "end", text="基本信息", open=True)
        self.desc_tree.insert(basic_node, "end", text=f"类型: {descriptor.get('type', '未知')}")
        self.desc_tree.insert(basic_node, "end", text=f"引用号(xref): {descriptor.get('xref', '未知')}")
        self.desc_tree.insert(basic_node, "end", text=f"嵌入状态: {'是' if descriptor.get('is_embedded', False) else '否'}")
        
        # 添加度量信息
        metrics = descriptor.get('metrics', {})
        if metrics:
            metrics_node = self.desc_tree.insert(font_node, "end", text="度量信息", open=True)
            
            # 定义度量显示顺序和显示名称
            metrics_display = [
                ("ascent", "上升部分"),
                ("descent", "下降部分"),
                ("capheight", "大写字母高度"),
                ("xheight", "x高度"),
                ("italicangle", "斜体角度"),
                ("stemv", "垂直笔画宽度"),
                ("stemh", "水平笔画宽度"),
                ("fontweight", "字重"),
                ("fontbbox", "字体边界框"),
                ("flags", "字体标志")
            ]
            
            # 按照指定的顺序显示度量信息
            for key, display_name in metrics_display:
                if key in metrics:
                    value = metrics[key]
                    # 对于数组类型的值，格式化显示
                    if isinstance(value, list):
                        value_str = f"[{', '.join(map(str, value))}]"
                    else:
                        value_str = str(value)
                    
                    # 直接显示度量信息
                    self.desc_tree.insert(metrics_node, "end", text=f"{display_name}: {value_str}")
            
            # 显示其他未列出的度量信息
            known_keys = {key for key, _ in metrics_display}
            for key, value in metrics.items():
                if key.lower() not in known_keys:
                    # 将键名转换为更友好的显示名称
                    display_name = key.replace('_', ' ').title()
                    
                    # 对于数组类型的值，格式化显示
                    if isinstance(value, list):
                        value_str = f"[{', '.join(map(str, value))}]"
                    else:
                        value_str = str(value)
                    
                    # 直接显示度量信息
                    self.desc_tree.insert(metrics_node, "end", text=f"{display_name}: {value_str}")
        
        # 添加原始信息
        raw_info = descriptor.get('raw_info', {})
        if raw_info:
            raw_node = self.desc_tree.insert(font_node, "end", text="原始信息", open=False)
            
            # 分组显示不同类型的信息
            info_groups = {
                "FontDescriptor": [],   # 字体描述符信息
                "DescendantFont": [],  # 后代字体信息
                "General": []           # 一般信息
            }
            
            # 分类所有原始信息
            for key, value in sorted(raw_info.items()):
                if key.startswith("FontDescriptor."):
                    # 字体描述符信息
                    display_key = key.replace("FontDescriptor.", "")
                    info_groups["FontDescriptor"].append((display_key, value))
                elif key.startswith("DescendantFont."):
                    # 后代字体信息
                    display_key = key.replace("DescendantFont.", "")
                    info_groups["DescendantFont"].append((display_key, value))
                else:
                    # 一般信息
                    info_groups["General"].append((key, value))
            
            # 显示一般信息
            if info_groups["General"]:
                general_node = self.desc_tree.insert(raw_node, "end", text="一般信息", open=True)
                for key, value in info_groups["General"]:
                    # 直接显示信息
                    self.desc_tree.insert(general_node, "end", text=f"{key}: {str(value)}")
            
            # 显示字体描述符信息
            if info_groups["FontDescriptor"]:
                fd_node = self.desc_tree.insert(raw_node, "end", text="字体描述符信息", open=True)
                for key, value in info_groups["FontDescriptor"]:
                    # 直接显示信息
                    self.desc_tree.insert(fd_node, "end", text=f"{key}: {str(value)}")
            
            # 显示后代字体信息
            if info_groups["DescendantFont"]:
                df_node = self.desc_tree.insert(raw_node, "end", text="后代字体信息", open=True)
                for key, value in info_groups["DescendantFont"]:
                    # 直接显示信息
                    self.desc_tree.insert(df_node, "end", text=f"{key}: {str(value)}")
    
    def _on_tree_select(self, event):
        """处理树形视图选择事件"""
        selection = self.desc_tree.selection()
        if selection:
            self.selected_item = selection[0]
        else:
            self.selected_item = None
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        # 获取点击位置的项目
        item = self.desc_tree.identify_row(event.y)
        if item:
            # 选中点击的项目
            self.desc_tree.selection_set(item)
            self.selected_item = item
            # 显示右键菜单
            self.desc_tree_menu.post(event.x_root, event.y_root)
    
    def _copy_as_json(self):
        """将选中的字体描述符信息复制为JSON格式"""
        if not self.selected_item:
            return
        
        # 获取选中项目的数据
        data = self._get_item_data(self.selected_item)
        
        if data:
            # 转换为JSON格式
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 复制到剪贴板
            self.root.clipboard_clear()
            self.root.clipboard_append(json_data)
            
            # 显示成功消息
            self.status_var.set("已复制选中项目的JSON数据到剪贴板")
    
    def _get_item_data(self, item):
        """递归获取项目及其子项目的数据"""
        # 获取项目文本
        text = self.desc_tree.item(item, "text")
        
        # 检查是否为根节点
        if item == "":
            return None
        
        # 检查是否为字体节点
        if text.startswith("字体:"):
            # 获取当前选中的字体名称
            font_name = text.replace("字体: ", "")
            if font_name in self.desc_map:
                return self.desc_map[font_name]
            return None
        
        # 检查是否为分组节点（基本信息、度量信息、原始信息）
        if text in ["基本信息", "度量信息", "原始信息", "一般信息", "字体描述符信息", "后代字体信息"]:
            # 获取所有子项目
            result = {}
            for child in self.desc_tree.get_children(item):
                child_text = self.desc_tree.item(child, "text")
                # 如果子项目是键值对，则提取它
                if ": " in child_text:
                    key, value = child_text.split(": ", 1)
                    # 尝试将值转换为适当的类型
                    result[key] = self._convert_value(value)
                else:
                    # 递归获取子项目的数据
                    child_data = self._get_item_data(child)
                    if child_data:
                        result[child_text] = child_data
            return result
        
        # 检查是否为键值对
        if ": " in text:
            key, value = text.split(": ", 1)
            return {key: self._convert_value(value)}
        
        # 如果是其他类型的节点，尝试获取子节点
        children = self.desc_tree.get_children(item)
        if children:
            result = {}
            for child in children:
                child_text = self.desc_tree.item(child, "text")
                child_data = self._get_item_data(child)
                if child_data:
                    if isinstance(child_data, dict) and len(child_data) == 1 and ": " in child_text:
                        # 如果子项目是单个键值对，直接使用其键值
                        key, _ = child_text.split(": ", 1)
                        result[key] = list(child_data.values())[0]
                    else:
                        result[child_text] = child_data
            return result
        
        # 如果没有子节点，返回文本本身
        return text
    
    def _convert_value(self, value_str):
        """将字符串值转换为适当的类型"""
        # 尝试转换为数字
        try:
            # 检查是否为整数
            if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
                return int(value_str)
            # 检查是否为浮点数
            if re.match(r'^-?\d+\.\d+$', value_str):
                return float(value_str)
        except ValueError:
            pass
        
        # 检查是否为布尔值
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # 检查是否为数组
        if value_str.startswith('[') and value_str.endswith(']'):
            try:
                # 尝试解析数组
                array_str = value_str[1:-1].strip()
                if not array_str:
                    return []
                
                # 分割数组元素
                elements = [e.strip() for e in array_str.split(',')]
                
                # 递归转换每个元素
                return [self._convert_value(e) for e in elements]
            except Exception:
                pass
        
        # 如果无法转换，返回原始字符串
        return value_str
    
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
