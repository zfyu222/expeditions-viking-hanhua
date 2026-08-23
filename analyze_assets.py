#!/usr/bin/env python3
"""
分析 Unity 5.6 assets 文件结构，找到需要扩展的 TextAsset 的数据偏移
"""

import struct
import os

ASSETS_FILE = r"D:\StaticHanHua\Projects\Expeditions Viking\Game\Expeditions Viking_Data\resources.assets"

def read_assets_header(data):
    """读取 Unity assets 文件头部"""
    offset = 0
    
    # 1. 元数据大小
    metadata_size = struct.unpack_from("<I", data, offset)[0]
    print(f"metadata_size: {metadata_size}")
    offset += 4
    
    # 2. 文件大小
    file_size = struct.unpack_from("<I", data, offset)[0]
    print(f"file_size: {file_size}")
    offset += 4
    
    # 3. 格式版本
    format_version = struct.unpack_from("<I", data, offset)[0]
    print(f"format_version: {format_version}")
    offset += 4
    
    # 4. 数据偏移（第一个文件偏移，指向对象数据开始位置）
    data_offset = struct.unpack_from("<I", data, offset)[0]
    print(f"data_offset (first file offset): {data_offset}")
    offset += 4
    
    # 5. Endianness (0=little)
    endian = data[offset]
    print(f"endianness: {endian}")
    offset += 1
    
    # 6. 保留字节
    reserved = data[offset:offset+3]
    offset += 3
    
    # 7. Unity 版本字符串（以 null 结尾）
    version_end = data.find(b'\x00', offset)
    version_str = data[offset:version_end].decode("ascii")
    print(f"unity_version: {version_str}")
    offset = version_end + 1
    
    return offset, metadata_size, file_size, format_version, data_offset


def find_textasset_in_header(data, header_offset, metadata_size):
    """在 TypeTree 区域中搜索 TextAsset 名称，获取其在文件中的 data_offset"""
    results = {}
    target_names = ["DialogueEnglish", "CharacterNamesEnglish", "InputEnglish"]
    
    for name in target_names:
        name_bytes = name.encode("utf-8")
        # 在文件中搜索名称
        pos = 0
        while True:
            idx = data.find(name_bytes, pos)
            if idx == -1:
                break
            
            # 检查前面4字节是否是长度前缀
            if idx >= 4:
                prefix = struct.unpack_from("<I", data, idx - 4)[0]
                if prefix == len(name_bytes):
                    # 找到了名称！现在分析这个位置周围的结构
                    results[name] = idx
                    break
            
            pos = idx + 1
    
    return results


def analyze_file():
    with open(ASSETS_FILE, "rb") as f:
        data = f.read()
    
    print(f"文件总大小: {len(data)} bytes")
    print()
    
    offset, metadata_size, file_size, format_version, data_offset = read_assets_header(data)
    print(f"\n头部解析到偏移: {offset}")
    print(f"对象数据起始偏移: {data_offset}")
    
    # 搜索目标名称
    print("\n=== 搜索目标 TextAsset 名称 ===")
    names = find_textasset_in_header(data, offset, metadata_size)
    
    for name, pos in names.items():
        print(f"\n{name}: 名称在偏移 0x{pos:X}")
        # 名称结构: [4字节长度][名称][对齐到4字节]
        name_len = len(name)
        name_data_start = pos + name_len
        # 对齐
        aligned = (name_data_start + 3) & ~3
        
        # 读取 m_Script 数组大小
        if aligned + 4 <= len(data):
            script_size = struct.unpack_from("<I", data, aligned)[0]
            script_start = aligned + 4
            print(f"  m_Script 大小: {script_size} bytes")
            print(f"  m_Script 数据偏移: 0x{script_start:X}")
            print(f"  数据前20字节: {data[script_start:script_start+20]}")
    
    # 搜索所有 4 字节对齐后的 m_Script 大小标记
    print("\n=== 数据偏移分析 ===")
    # DialogueEnglish 名称在文件中的位置
    if "DialogueEnglish" in names:
        de_pos = names["DialogueEnglish"]
        de_aligned = ((de_pos + len("DialogueEnglish")) + 3) & ~3
        de_script_size = struct.unpack_from("<I", data, de_aligned)[0]
        de_data_start = de_aligned + 4
        de_data_end = de_data_start + de_script_size
        
        print(f"DialogueEnglish 数据范围: 0x{de_data_start:X} - 0x{de_data_end:X}")
        print(f"  数据结束在文件中的位置: 0x{de_data_end:X}")
        print(f"  文件剩余: {len(data) - de_data_end} bytes")
        
        # 检查 DialogueEnglish 后面是什么
        after_dialogue = data[de_data_end:de_data_end+100]
        print(f"  后续数据: {after_dialogue[:50]}")
        
        # 在 DialogueEnglish 数据后面搜索下一个名称
        # 这可以帮助判断是否需要更新偏移表
        next_struct = data[de_data_end:de_data_end+20]
        print(f"  后续结构头: {next_struct.hex()}")


if __name__ == "__main__":
    analyze_file()
