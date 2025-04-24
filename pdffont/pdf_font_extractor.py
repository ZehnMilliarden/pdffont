import io
import fitz
import os
import sys
import platform

class PdfFontExtractor:
    """PDF字体提取器类，专注于从PDF文件中提取字体"""
    
    def __init__(self, path=None):
        """初始化PDF字体提取器
        
        参数:
            path: PDF文件路径，可选
        """
        self.__path__ = path
        self.__docs__ = None
        self.__fonts__ = []
        self.__font_dirs = []
        if path:
            self.open(path)
        self.__load_font_dir()
    
    def __load_font_dir(self):
        # 根据操作系统确定字体目录
        self.__font_dirs = []
        
        # Windows字体目录
        if platform.system() == "Windows":
            self.__font_dirs.extend([
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Fonts"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
                "C:\\Windows\\Fonts"
            ])
        
        # macOS字体目录
        elif platform.system() == "Darwin":
            self.__font_dirs.extend([
                "/Library/Fonts",
                "/System/Library/Fonts",
                os.path.expanduser("~/Library/Fonts")
            ])
        
        # Linux字体目录
        else:
            self.__font_dirs.extend([
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts"),
                os.path.expanduser("~/.local/share/fonts")
            ])
        
        # 添加当前目录和子目录
        self.__font_dirs.append(os.getcwd())
        self.__font_dirs.append(os.path.join(os.getcwd(), "fonts"))

    def open(self, path):
        """打开PDF文件
        
        参数:
            path: PDF文件路径
        """
        self.__path__ = path
        if self.__docs__:
            self.__docs__.close()
        self.__docs__ = fitz.open(path)
        self.__fonts__ = []
        return True
    
    def close(self):
        """关闭PDF文件"""
        if self.__docs__:
            self.__docs__.close()
            self.__docs__ = None
    
    def __del__(self):
        """析构函数，确保关闭文档"""
        self.close()
    
    def extract_fonts(self):
        """提取PDF中的所有字体，并返回字体对象列表"""
        if not self.__docs__:
            raise ValueError("未打开PDF文件")
            
        font_objects = []
        unique_fonts = set()  # 用于跟踪已处理的字体，避免重复
        self.__fonts__ = []
        
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
            
            if not buffer:
                # 从本地字体目录中根据字体名称查找加载字体信息
                try:
                    # 尝试从多个可能的字体目录查找字体
                    buffer = self._find_font_in_system(basename, ext)
                    if buffer:
                        print(f"从系统字体目录加载: {basename}.{ext}")
                    else:
                        print(f"无法找到字体: {basename}.{ext}")
                        continue  # 如果找不到字体，跳过这个字体
                except Exception as e:
                    print(f"加载字体时出错: {e}")
                    continue
            
            # 检查是否为TTC字体文件
            is_ttc = False
            font_count = 1
            try:
                # 创建临时文件对象检查TTC头部
                temp_stream = io.BytesIO(buffer)
                temp_stream.seek(0)
                tag = temp_stream.read(4)
                if tag == b'ttcf':
                    from fontTools.ttLib.sfnt import readTTCHeader
                    temp_stream.seek(0)
                    ttc_header = readTTCHeader(temp_stream)
                    font_count = ttc_header.numFonts
                    is_ttc = True
                    print(f"检测到TTC字体文件，包含{font_count}个字体")
            except Exception as e:
                print(f"检查TTC文件格式时出错: {e}")
                font_count = 1
            
            # 处理字体文件
            for font_index in range(font_count):
                try:
                    # 在内存中处理字体
                    font_obj = self.process_font_in_memory(buffer, basename, ext, font_index)
                    if font_obj:
                        font_objects.append(font_obj)
                        print(f"字体信息: {font_obj.get('family_name', 'Unknown')} (索引: {font_index})")
                except Exception as e:
                    print(f"处理字体时出错 (索引: {font_index}): {e}")
            
        return font_objects
    
    def _map_font_name_to_font_file(self, font_name: str) -> str:
        """将字体名称映射到字体文件路径"""
        known_mappings = {
            # Times系列
            'Times New Roman': 'times',
            'TimesNewRomanPSMT': 'times',
            'TimesNewRomanPS-BoldMT': 'timesbd',
            'TimesNewRomanPS-ItalicMT': 'timesi',
            'TimesNewRomanPS-BoldItalicMT': 'timesbi',
            
            # Arial系列
            'Arial': 'arial',
            'ArialMT': 'arial',
            'Arial-BoldMT': 'arialbd',
            'Arial-ItalicMT': 'ariali',
            'Arial-BoldItalicMT': 'arialbi',
            'Arial Black': 'ariblk',
            'Arial Narrow': 'arialn',
            'Arial Unicode MS': 'arialuni',
            
            # 中文字体
            'Microsoft YaHei': 'msyh',
            'MicrosoftYaHei': 'msyh',
            '微软雅黑': 'msyh',
            'KaiTi': 'simkai',
            '楷体': 'simkai',
            'SimSun': 'simsun',
            '宋体': 'simsun',
            'FangSong': 'simfang',
            '仿宋': 'simfang',
            '隶书': 'simli',
            '黑体': 'simhei',
            
            # 其他常用字体
            'Cambria': 'cambria',
            'Cambria Math': 'cambria',
            'Calibri': 'calibri',
            'Consolas': 'consola',
            'Courier New': 'cour',
            'CourierNewPSMT': 'cour',
            'Courier': 'cour',
            'Georgia': 'georgia',
            'Tahoma': 'tahoma',
            'Verdana': 'verdana',
            'Wingdings': 'wingding',
            'Wingdings 2': 'wingdng2',
            'Wingdings 3': 'wingdng3',
            'Symbol': 'symbol',
            'Webdings': 'webdings',
        }
        return known_mappings.get(font_name, font_name)

    def _find_font_in_system(self, basename, ext):
        """在系统字体目录中查找字体文件
        
        参数:
            basename: 字体基本名称
            ext: 字体文件扩展名，可能为空
            
        返回:
            字体文件的二进制数据，如果找不到则返回None
        """
        
        # 处理字体名称
        if "+" in basename:
            # 去除前缀，如"AAAAAA+"
            basename = basename.split("+", 1)[1]

        # 字体文件名称可能的变体
        possible_names = []
        
        basename = self._map_font_name_to_font_file(basename)

        # 如果扩展名不为空，添加带扩展名的文件名
        if ext and ext.strip() and ext != 'n/a':
            possible_names.extend([
                f"{basename}.{ext}",
                f"{basename}.{ext.lower()}",
                f"{basename}.{ext.upper()}",
            ])
        else:
            # 如果扩展名为空，添加常见的字体文件扩展名
            for common_ext in ["ttf", "otf", "ttc", "pfb", "woff", "woff2"]:
                possible_names.extend([
                    f"{basename}.{common_ext}",
                    f"{basename}.{common_ext.upper()}",
                ])
        
        # 添加不带扩展名的文件名（某些系统可能没有扩展名）
        possible_names.append(basename)
        
        # 遍历所有可能的字体目录和文件名
        for font_dir in self.__font_dirs:
            if not os.path.exists(font_dir) or not os.path.isdir(font_dir):
                continue
                
            # 递归搜索字体目录
            for root, _, files in os.walk(font_dir):
                for name in possible_names:
                    if name in files:
                        font_path = os.path.join(root, name)
                        try:
                            with open(font_path, "rb") as f:
                                print(f"找到字体文件: {font_path}")
                                return f.read()
                        except Exception as e:
                            print(f"读取字体文件出错 {font_path}: {e}")
                
                # 如果没有精确匹配，尝试模糊匹配
                if not ext or ext.strip() == "":
                    for file in files:
                        # 检查文件名是否包含基本名称（不区分大小写）
                        if basename.lower() in file.lower():
                            font_path = os.path.join(root, file)
                            try:
                                # 检查是否是字体文件（基于扩展名）
                                if any(file.lower().endswith(f".{e}") for e in ["ttf", "otf", "ttc", "pfb", "woff", "woff2"]):
                                    with open(font_path, "rb") as f:
                                        print(f"找到匹配字体文件: {font_path}")
                                        return f.read()
                            except Exception as e:
                                print(f"读取字体文件出错 {font_path}: {e}")
        
        # 如果是系统字体，尝试使用fontTools的findFont功能
        try:
            from fontTools.ttLib import TTFont
            from fontTools.ttLib.sfnt import readTTCHeader
            
            # 尝试使用fontTools的字体查找功能
            # 这里可以添加更多的字体查找逻辑
        except ImportError:
            pass
        
        return None
    
    def process_font_in_memory(self, buffer, basename, ext, font_index=0):
        """在内存中处理字体数据
        
        参数:
            buffer: 字体文件的二进制数据
            basename: 字体基本名称
            ext: 字体文件扩展名
            font_index: 字体索引，用于TTC文件
            
        返回:
            字体对象及相关信息的字典
        """
        try:
            # 使用fontTools库处理字体
            from fontTools.ttLib import TTFont, TTLibError
            from fontTools.ttLib.sfnt import readTTCHeader
            
            # 创建内存文件对象
            font_stream = io.BytesIO(buffer)
            
            # 检查是否是TTC文件
            is_ttc = False
            try:
                # 尝试读取TTC头部信息
                font_stream.seek(0)
                tag = font_stream.read(4)
                if tag == b'ttcf':
                    is_ttc = True
                    font_stream.seek(0)
                    ttc_header = readTTCHeader(font_stream)
                    num_fonts = ttc_header.numFonts
                    print(f"检测到TTC文件，包含{num_fonts}个字体")
                    if font_index >= num_fonts:
                        print(f"字体索引超出范围，应在0到{num_fonts-1}之间")
                        font_index = 0  # 默认使用第一个字体
            except Exception as e:
                print(f"检查TTC文件时出错: {e}")
                font_stream.seek(0)  # 重置文件指针
            
            # 从内存加载字体
            try:
                if is_ttc:
                    font = TTFont(font_stream, fontNumber=font_index)
                else:
                    font = TTFont(font_stream)
            except Exception as e:
                print(f"加载字体时出错: {e}")
                return None
            
            # 尝试获取字体名称信息
            family_name = None
            full_name = None
            supported_chars = []
            
            try:
                # 先尝试从文件名获取字体名称
                family_name = basename
                # 如果基本名称包含+号，去除前缀
                if "+" in family_name:
                    family_name = family_name.split("+", 1)[1]
                
                # 如果字体对象存在，尝试从字体获取更多信息
                if "name" in font:
                    try:
                        name_records = font["name"].names
                        for record in name_records:
                            if record.nameID == 1 and not family_name:  # Family name
                                try:
                                    if record.isUnicode():
                                        family_name = record.string.decode("utf-16-be")
                                    else:
                                        family_name = record.string.decode("latin1")
                                except:
                                    pass
                            
                            if record.nameID == 4 and not full_name:  # Full name
                                try:
                                    if record.isUnicode():
                                        full_name = record.string.decode("utf-16-be")
                                    else:
                                        full_name = record.string.decode("latin1")
                                except:
                                    pass
                    except Exception as e:
                        print(f"读取字体名称表时出错: {e}")
                
                # 尝试获取字体的字符映射表
                try:
                    if "cmap" in font:
                        cmap = font.getBestCmap()
                        if cmap:
                            supported_chars = list(cmap.keys())
                except Exception as e:
                    print(f"读取字体字符映射表时出错: {e}")
            except Exception as e:
                print(f"处理字体信息时出错: {e}")
            
            # 提取字体度量信息
            metrics = {}
            try:
                if "head" in font:
                    head_table = font["head"]
                    metrics["units_per_em"] = head_table.unitsPerEm
                    metrics["created"] = head_table.created
                    metrics["modified"] = head_table.modified
                    metrics["x_min"] = head_table.xMin
                    metrics["y_min"] = head_table.yMin
                    metrics["x_max"] = head_table.xMax
                    metrics["y_max"] = head_table.yMax
                
                if "hhea" in font:
                    hhea_table = font["hhea"]
                    metrics["ascent"] = hhea_table.ascent
                    metrics["descent"] = hhea_table.descent
                    metrics["line_gap"] = hhea_table.lineGap
                    metrics["advance_width_max"] = hhea_table.advanceWidthMax
                
                if "OS/2" in font:
                    os2_table = font["OS/2"]
                    metrics["weight_class"] = os2_table.usWeightClass
                    metrics["width_class"] = os2_table.usWidthClass
                    metrics["subscript_x_size"] = os2_table.ySubscriptXSize
                    metrics["subscript_y_size"] = os2_table.ySubscriptYSize
                    metrics["strikeout_size"] = os2_table.yStrikeoutSize
                    metrics["strikeout_position"] = os2_table.yStrikeoutPosition
                    
                    # 字体类型信息
                    if hasattr(os2_table, "fsType"):
                        metrics["embedding_rights"] = os2_table.fsType
                    
                    # 字体族信息
                    if hasattr(os2_table, "panose"):
                        panose = os2_table.panose
                        panose_dict = {}
                        
                        # 安全地获取Panose属性
                        for attr in ["bFamilyType", "bSerifStyle", "bWeight", "bProportion", 
                                      "bContrast", "bStrokeVariation", "bArmStyle", 
                                      "bLetterform", "bMidline", "bXHeight"]:
                            if hasattr(panose, attr):
                                panose_dict[attr.replace('b', '').lower()] = getattr(panose, attr)
                            
                        metrics["panose"] = panose_dict
            except Exception as e:
                print(f"提取字体度量信息时出错: {e}")
            
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
                "supported_chars": supported_chars,
                "metrics": metrics
            }
        except Exception as e:
            print(f"处理字体时出错: {e}")
            return None
        finally:
            if 'font_stream' in locals():
                font_stream.close()
    
    def extract_font_descriptors(self):
        """直接从 PDF 文件中提取字体描述符(FontDescriptor)信息
        
        返回:
            字体描述符列表，每个元素是一个字典，包含字体名称和字体描述符信息
        """
        if not self.__docs__:
            raise ValueError("未打开PDF文件")
            
        font_descriptors = []
        processed_xrefs = set()  # 记录已处理的xref
        
        # 遍历所有页面
        for page_index, page in enumerate(self.__docs__):
            # 获取页面上的所有字体
            fonts = page.get_fonts(full=True)
            
            for font in fonts:
                xref = font[0]  # 字体引用号
                font_type = font[1]  # 字体类型
                font_name = font[3]  # 字体名称
                
                # 跳过已处理过的字体
                if xref in processed_xrefs:
                    continue
                
                processed_xrefs.add(xref)
                
                # 初始化字体描述符字典
                descriptor_info = {
                    "xref": xref,
                    "type": font_type,
                    "name": font_name,
                    "is_embedded": xref != 0,
                    "raw_info": {},
                    "metrics": {}
                }
                
                # 直接从 PDF 文档中提取字体描述符信息
                try:
                    # 获取字体对象
                    if xref == 0:
                        continue  # 跳过非嵌入字体
                    
                    # 获取字体对象
                    font_obj = self.__docs__.xref_object(xref, compressed=True)
                    if not font_obj:
                        continue
                    
                    # 存储原始内容
                    if isinstance(font_obj, str):
                        descriptor_info["raw_info"]["RawContent"] = font_obj
                    elif isinstance(font_obj, dict):
                        for key, value in font_obj.items():
                            descriptor_info["raw_info"][key] = str(value)
                    
                    # 判断是否为Type0字体
                    is_type0 = False
                    if isinstance(font_obj, str):
                        is_type0 = "/Subtype/Type0" in font_obj
                    elif isinstance(font_obj, dict):
                        is_type0 = font_obj.get("Subtype") == "Type0"
                    
                    # 如果是Type0字体，直接获取DescendantFonts引用
                    if is_type0:
                        # 从字符串或字典中提取DescendantFonts引用
                        descendant_ref = None
                        
                        if isinstance(font_obj, str):
                            # 使用正则表达式提取引用
                            import re
                            match = re.search(r"/DescendantFonts\s*\[\s*(\d+)\s+0\s+R\s*\]", font_obj)
                            if match:
                                descendant_ref = int(match.group(1))
                        elif isinstance(font_obj, dict) and "DescendantFonts" in font_obj:
                            # 从字典中提取引用
                            descendant_fonts = font_obj["DescendantFonts"]
                            if isinstance(descendant_fonts, list) and len(descendant_fonts) > 0:
                                ref_str = str(descendant_fonts[0])
                                if " 0 R" in ref_str:
                                    descendant_ref = int(ref_str.split(" ")[0])
                        
                        # 如果找到了DescendantFonts引用，获取其内容
                        if descendant_ref:
                            print(f"找到DescendantFonts引用: {descendant_ref}")
                            descendant_obj = self.__docs__.xref_object(descendant_ref, compressed=True)
                            
                            # 处理后代字体对象
                            if descendant_obj:
                                # 存储后代字体信息
                                if isinstance(descendant_obj, str):
                                    descriptor_info["raw_info"]["DescendantFont"] = descendant_obj
                                elif isinstance(descendant_obj, dict):
                                    for key, value in descendant_obj.items():
                                        descriptor_info["raw_info"][f"DescendantFont.{key}"] = str(value)
                                
                                # 从后代字体中提取FontDescriptor引用
                                fd_ref = None
                                
                                if isinstance(descendant_obj, str):
                                    # 使用正则表达式提取引用
                                    match = re.search(r"/FontDescriptor\s+(\d+)\s+0\s+R", descendant_obj)
                                    if match:
                                        fd_ref = int(match.group(1))
                                elif isinstance(descendant_obj, dict) and "FontDescriptor" in descendant_obj:
                                    # 从字典中提取引用
                                    fd_ref_str = str(descendant_obj["FontDescriptor"])
                                    if " 0 R" in fd_ref_str:
                                        fd_ref = int(fd_ref_str.split(" ")[0])
                                
                                # 如果找到了FontDescriptor引用，获取其内容
                                if fd_ref:
                                    print(f"找到FontDescriptor引用: {fd_ref}")
                                    fd_obj = self.__docs__.xref_object(fd_ref, compressed=True)
                                    
                                    # 处理字体描述符对象
                                    self._process_font_descriptor(fd_obj, descriptor_info)
                    
                    # 如果不是Type0字体，直接在当前字体对象中查找FontDescriptor
                    else:
                        fd_ref = None
                        
                        if isinstance(font_obj, str):
                            # 使用正则表达式提取引用
                            match = re.search(r"/FontDescriptor\s+(\d+)\s+0\s+R", font_obj)
                            if match:
                                fd_ref = int(match.group(1))
                        elif isinstance(font_obj, dict) and "FontDescriptor" in font_obj:
                            # 从字典中提取引用
                            fd_ref_str = str(font_obj["FontDescriptor"])
                            if " 0 R" in fd_ref_str:
                                fd_ref = int(fd_ref_str.split(" ")[0])
                        
                        # 如果找到了FontDescriptor引用，获取其内容
                        if fd_ref:
                            print(f"找到FontDescriptor引用: {fd_ref}")
                            fd_obj = self.__docs__.xref_object(fd_ref, compressed=True)
                            
                            # 处理字体描述符对象
                            self._process_font_descriptor(fd_obj, descriptor_info)
                    
                    # 提取字体名称
                    if "BaseFont" in descriptor_info["raw_info"]:
                        descriptor_info["family_name"] = descriptor_info["raw_info"]["BaseFont"]
                    
                    # 添加到结果中
                    font_descriptors.append(descriptor_info)
                except Exception as e:
                    print(f"提取字体描述符时出错: {e} (xref: {xref}): {e}")
        
        return font_descriptors
    
    def _process_font_descriptor(self, fd_obj, descriptor_info):
        """处理字体描述符对象
        
        参数:
            fd_obj: 字体描述符对象
            descriptor_info: 字体描述符信息字典
        """
        try:
            # 存储原始内容
            if isinstance(fd_obj, str):
                descriptor_info["raw_info"]["FontDescriptor"] = fd_obj
            elif isinstance(fd_obj, dict):
                for key, value in fd_obj.items():
                    descriptor_info["raw_info"][f"FontDescriptor.{key}"] = str(value)
            
            # 提取字体度量信息
            self._extract_metrics_from_string(str(fd_obj), descriptor_info["metrics"])
        except Exception as e:
            print(f"处理字体描述符时出错: {e}")
    
    def _extract_numeric_value(self, text, key):
        """从字符串中提取数值
        
        参数:
            text: 要解析的字符串
            key: 要提取的关键字
            
        返回:
            提取的数值，如果无法提取则返回None
        """
        try:
            # 尝试不同的模式匹配
            patterns = [
                f"/{key} (-?\d+(\.\d+)?)",  # 如 /Ascent 800
                f"/{key}/(-?\d+(\.\d+)?)",  # 如 /Ascent/800
                f"/{key}\s+(-?\d+(\.\d+)?)",  # 如 /Ascent 800
                f"{key}\s+(-?\d+(\.\d+)?)"  # 如 Ascent 800
            ]
            
            import re
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return float(match.group(1))
            
            return None
        except Exception as e:
            print(f"提取{key}数值时出错: {e}")
            return None
    
    def _extract_array_value(self, text, key):
        """从字符串中提取数组值
        
        参数:
            text: 要解析的字符串
            key: 要提取的关键字
            
        返回:
            提取的数组，如果无法提取则返回None
        """
        try:
            # 尝试不同的模式匹配
            patterns = [
                f"/{key}\s*\[([^\]]+)\]",  # 如 /FontBBox [-1000 -300 1000 1000]
                f"/{key}/\[([^\]]+)\]",  # 如 /FontBBox/[-1000 -300 1000 1000]
                f"{key}\s*\[([^\]]+)\]"  # 如 FontBBox [-1000 -300 1000 1000]
            ]
            
            import re
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    # 提取数组内容并转换为数字列表
                    array_str = match.group(1).strip()
                    return [float(x) for x in array_str.split() if x.strip()]
            
            return None
        except Exception as e:
            print(f"提取{key}数组时出错: {e}")
            return None
    
    def _extract_metrics_from_string(self, text, metrics_dict):
        """从字符串中提取字体度量信息并添加到字典中
        
        参数:
            text: 要解析的字符串
            metrics_dict: 要填充的度量信息字典
        """
        try:
            # 提取常见的度量信息
            metrics_keys = {
                "Ascent": "ascent",
                "Descent": "descent",
                "CapHeight": "capheight",
                "XHeight": "xheight",
                "ItalicAngle": "italicangle",
                "StemV": "stemv",
                "StemH": "stemh",
                "FontWeight": "fontweight",
                "Flags": "flags"
            }
            
            # 提取数值类型的度量
            for key, dict_key in metrics_keys.items():
                value = self._extract_numeric_value(text, key)
                if value is not None:
                    metrics_dict[dict_key] = value
            
            # 提取FontBBox数组
            fontbbox = self._extract_array_value(text, "FontBBox")
            if fontbbox is not None:
                metrics_dict["fontbbox"] = fontbbox
                
            # 打印提取的度量信息
            print(f"从字符串中提取的度量信息: {metrics_dict}")
        except Exception as e:
            print(f"从字符串中提取度量信息时出错: {e}")
    
    def render_text_with_font(self, buffer, text, size=24, font_color=(0, 0, 0), bg_color=(255, 255, 255)):
        """使用指定字体渲染文本并返回图像
        
        参数:
            buffer: 字体文件的二进制数据
            text: 要渲染的文本
            size: 字体大小
            font_color: 字体颜色，默认黑色
            bg_color: 背景颜色，默认白色
            
        返回:
            PIL Image对象
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建内存中的字体对象
            font_stream = io.BytesIO(buffer)
            
            try:
                # 尝试加载字体
                font = ImageFont.truetype(font_stream, size)
            except Exception as e:
                print(f"加载字体进行渲染时出错: {e}")
                # 如果加载失败，使用系统默认字体
                try:
                    # 尝试使用默认字体
                    font = ImageFont.load_default()
                    print("使用系统默认字体")
                except Exception:
                    # 如果还是失败，返回错误
                    print("无法加载任何字体")
                    return None
            
            # 计算文本尺寸以确定图像大小
            text_width = 300  # 默认宽度
            text_height = size * 2  # 默认高度
            
            try:
                # 尝试不同的方法获取文本尺寸
                try:
                    # 老版方法
                    text_width, text_height = font.getsize(text)
                except AttributeError:
                    # 新版Pillow使用getbbox
                    try:
                        bbox = font.getbbox(text)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except (AttributeError, TypeError):
                        # 如果还是失败，尝试使用getlength
                        try:
                            text_width = font.getlength(text)
                            text_height = size * 1.5  # 估计高度
                        except (AttributeError, TypeError):
                            # 如果所有方法都失败，使用默认值
                            text_width = len(text) * size * 0.7  # 根据文本长度和字体大小估计
                            text_height = size * 1.5
            except Exception as e:
                print(f"计算文本尺寸时出错: {e}")
                # 使用默认值
                text_width = max(300, len(text) * size * 0.7)
                text_height = size * 1.5
            
            # 添加边距
            img_width = int(text_width + 40)
            img_height = int(text_height + 40)
            
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
