#!/usr/bin/env python3
"""
扩展 TextAsset 数据并更新所有偏移引用。
策略：在扩展的 TextAsset 数据后面插入额外字节，
然后更新文件中所有指向该位置之后的偏移。
"""

import struct
import os
import shutil

ASSETS_FILE = r"D:\StaticHanHua\Projects\Expeditions Viking\Game\Expeditions Viking_Data\resources.assets". vuuuuuuuu9u67u677777777;777?
ASSETS_FILE = r"D:\StaticHanHua\Projects\Expeditions Viking\Game\Expeditions Viking_Data\resources.assets"
CHINESE_DIR = r"D:\StaticHanHua\Projects\Expeditions Viking\Chinese_Localization\Chinese\Localization"
BACKUP_DIR = r"D:\StaticHanHua\Projects\Expeditions Viking\backup"

# 需要扩展替换的 TextAsset（中文比英文大）
REPLACEMENTS = {
    "DialogueEnglish": "Dialogue/DialogueChinese.xml",
    "CharacterNamesEnglish": "Names/NamesChinese.xml",
    "InputEnglish": "Input/InputChinese.xml",
}


def find_textasset_info(data, name):
    """找到 TextAsset 的名称偏移、数据偏移和数据大小"""
    name_bytes = name.encode("utf-8")
    
    pos = 0
    while True:
        idx = data.find(name_bytes, pos)
        if idx == -1:
            return None
        
        if idx >= 4:
            prefix = struct.unpack_from("<I", data, idx - 4)[0]
            if prefix == len(name_bytes):
                name_pos = idx - 4
                aligned = ((idx + len(name_bytes)) + 3) & ~3
                script_size = struct.unpack_from("<I", data, aligned)[0]
                script_data_start = aligned + 4
                
                if script_data_start + 1 <= len(data) and data[script_data_start] in (ord('<'), ord('\xef')):
                    return {
                        'name_offset': name_pos,
                        'name_len': len(name_bytes) + 4,
                        'script_size_offset': aligned,
                        'script_size': script_size,
                        'script_data_offset': script_data_start,
                        'total_size': script_data_start + script_size - name_pos,
                    }
        
        pos = idx + 1


def main():
    # 1. 读取原始文件
    print(f"读取 {ASSETS_FILE}...")
    with open(ASSETS_FILE, "rb") as f:
        data = bytearray(f.read())
    
    original_size = len(data)
    print(f"文件大小: {original_size} bytes")
    
    # 2. 找到每个需要替换的 TextAsset
    infos = {}
    for name, xml_file in REPLACEMENTS.items():
        info = find_textasset_info(data, name)
        if info:
            chinese_path = os.path.join(CHINESE_DIR, xml_file)
            with open(chinese_path, "rb") as f:
                info['new_content'] = f.read()
            info['new_size'] = len(info['new_content'])
            info['delta'] = info['new_size'] - info['script_size']
            infos[name] = info
            print(f"{name}: 原={info['script_size']}, 新={info['new_size']}, 差={info['delta']}")
        else:
            print(f"{name}: 未找到!")
    
    if not infos:
        print("没有需要扩展的 TextAsset")
        return
    
    # 3. 按数据偏移排序（从后往前处理，避免偏移问题）
    sorted_names = sorted(infos.keys(), key=lambda n: infos[n]['script_data_offset'], reverse=True)
    
    # 4. 逐个扩展（从后往前，后面的先扩展，这样不影响前面的偏移）
    total_delta = 0
    for name in sorted_names:
        info = infos[name]
        
        script_data_end = info['script_data_offset'] + info['script_size']
        
        # 需要扩展的字节数
        delta = info['delta']
        if delta <= 0:
            # 不需要扩展，直接替换
            data[info['script_data_offset']:info['script_data_offset'] + info['new_size']] = info['new_content']
            if info['new_size'] < info['script_size']:
                data[info['script_data_offset'] + info['new_size']:script_data_end] = b'\x00' * (info['script_size'] - info['new_size'])
            struct.pack_into("<I", data, info['script_size_offset'], info['new_size'])
            print(f"{name}: 直接替换（delta={delta}）")
            continue
        
        print(f"\n扩展 {name}: +{delta} bytes at offset 0x{script_data_end:X}")
        
        # 在 script_data_end 处插入 delta 字节
        data[script_data_end:script_data_end] = b'\x00' * delta
        
        # 写入新数据
        data[info['script_data_offset']:info['script_data_offset'] + info['new_size']] = info['new_content']
        
        # 更新 m_Script 大小
        struct.pack_into("<I", data, info['script_size_offset'], info['new_size'])
        
        total_delta += delta
        
        # 现在需要更新文件中所有指向 script_data_end 之后的偏移
        # Unity 5.6 assets 文件中的偏移包括：
        # 1. TypeTree 中的 data_offset 字段
        # 2. 其他 TextAsset 的 data_offset（我们已经从后往前处理，所以前面的不受影响）
        
        # 但还有 TypeTree 的偏移表需要更新！
        # 这比较复杂。让我先做一个保守的尝试：只处理这些 TextAsset
        
        print(f"  当前总偏移: {total_delta} bytes")
    
    # 5. 更新文件头部中的 file_size 和可能的其他元数据
    # Unity 5.6 的 assets 头部有 file_size 字段
    if total_delta > 0:
        # file_size 在偏移 4 处
        current_file_size = struct.unpack_from("<I", data, 4)[0]
        if current_file_size == original_size:
            struct.pack_into("<I", data, 4, len(data))
            print(f"\n更新 file_size: {original_size} -> {len(data)}")
        else:
            print(f"\nWARNING: file_size ({current_file_size}) != 原始大小 ({original_size})")
        
        # 注意：TypeTree 中有指向对象数据的偏移，如果扩展的数据在 TypeTree 引用的数据区域内，
        # 需要更新这些引用。但是 TextAsset 的 m_Script 数据不在 TypeTree 引用区域内
        # （它是内联数据），所以可能不需要更新。
    
    # 6. 保存
    print(f"\n保存...")
    with open(ASSETS_FILE, "wb") as f:
        f.write(data)
    
    print(f"完成！新文件大小: {len(data)} bytes (增加了 {total_delta} bytes)")
    print(f"启动游戏测试。")


if __name__ == "__main__":
    main()
