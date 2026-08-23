#!/usr/bin/env python3
"""
Expeditions Viking 汉化 - 第2步：AI 批量翻译
使用 DeepSeek API 将 CSV 中的英文翻译为中文
"""

import os
import csv
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# DeepSeek API 配置
API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk-e212fed0045a45948cb612689f992f45"
MODEL = "deepseek-v4-flash"

INPUT_CSV = os.path.join(BASE_DIR, "extracted_strings.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "translated_strings.csv")
PROGRESS_FILE = os.path.join(BASE_DIR, "translation_progress.json")

BATCH_SIZE = 20  # 每批翻译的条数
MAX_WORKERS = 4  # 并发线程数
MAX_RETRIES = 3  # 最大重试次数


def load_entries():
    """加载待翻译的条目"""
    entries = []
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries


def save_progress(translated_map):
    """保存翻译进度"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(translated_map, f, ensure_ascii=False, indent=2)


def load_progress():
    """加载已翻译的进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def translate_batch(texts, retry_count=0):
    """调用 DeepSeek API 翻译一批文本"""
    # 构建翻译提示词
    prompt_lines = []
    for i, text in enumerate(texts):
        prompt_lines.append(f"{i+1}. {text}")
    
    system_prompt = """你是一名专业的中文游戏翻译家。你的任务是把英文游戏文本翻译成简体中文。

翻译原则：
1. 忠实准确地翻译，保持原文的语气和风格
2. 保留原文中的格式化标签，如 [i]、[/i]、[color="xxx"]、[/color]、[size="xx"]、[/size]、{xxx}、<xxx> 等
3. 保留原文中的换行符 \\n
4. 对于维京/Norse 专有名词（人名、地名），保留原文或在首次出现时附注中文
5. 对话文本要口语化、自然流畅
6. UI文本要简洁明了
7. 技能/物品描述要准确

输出格式：每行一个翻译结果，以 "序号. 译文" 的格式输出，不要添加任何其他内容。"""

    user_message = "\n".join(prompt_lines)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请将以下英文游戏文本翻译成简体中文：\n\n{user_message}"}
        ],
        "temperature": 1.0,
        "max_tokens": 4096
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 解析返回的翻译结果
        translations = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # 匹配 "序号. 译文" 格式
            # 可能格式：1. 译文 或 1.译文 或 1、译文
            import re
            match = re.match(r'^(\d+)[\.\、\s)]+\s*(.*)', line)
            if match:
                translations.append(match.group(2))
        
        # 如果解析出的数量不对，尝试简单分割
        if len(translations) != len(texts):
            # 回退：按行分割，每行去掉序号前缀
            translations = []
            for line in content.strip().split("\n"):
                line = line.strip()
                if line:
                    match = re.match(r'^(\d+)[\.\、\s)]+\s*(.*)', line)
                    if match:
                        translations.append(match.group(2))
                    else:
                        translations.append(line)
        
        return translations[:len(texts)]
    
    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f"  重试 {retry_count + 1}/{MAX_RETRIES}: {e}")
            time.sleep(2 * (retry_count + 1))
            return translate_batch(texts, retry_count + 1)
        else:
            print(f"  翻译失败: {e}")
            return [""] * len(texts)


def main():
    print("加载待翻译文本...")
    entries = load_entries()
    total = len(entries)
    print(f"共 {total} 条待翻译")

    # 加载进度
    progress = load_progress()
    translated_count = len(progress)
    print(f"已翻译: {translated_count} 条")

    # 找出未翻译的条目
    pending = []
    for entry in entries:
        key = entry["key"]
        if key not in progress:
            pending.append(entry)

    if not pending:
        print("所有文本已翻译完成！")
    else:
        print(f"待翻译: {len(pending)} 条，预计批次: {len(pending) // BATCH_SIZE + 1}")
        
        # 分批翻译
        for batch_start in range(0, len(pending), BATCH_SIZE):
            batch = pending[batch_start:batch_start + BATCH_SIZE]
            texts = [entry["原文"] for entry in batch]
            
            batch_num = batch_start // BATCH_SIZE + 1
            total_batches = len(pending) // BATCH_SIZE + 1
            print(f"翻译批次 {batch_num}/{total_batches} ({len(texts)} 条)...")
            
            translations = translate_batch(texts)
            
            # 保存结果
            for entry, translation in zip(batch, translations):
                progress[entry["key"]] = translation
            
            # 每批次保存进度
            save_progress(progress)
            
            # 避免请求过快
            time.sleep(0.5)

    # 生成翻译后的 CSV
    print("\n生成翻译结果 CSV...")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "原文", "译文", "category"])
        for entry in entries:
            key = entry["key"]
            translation = progress.get(key, "")
            writer.writerow([key, entry["原文"], translation, entry["category"]])

    translated_real = sum(1 for v in progress.values() if v.strip())
    print(f"\n翻译完成！")
    print(f"总条目: {total}")
    print(f"已翻译: {translated_real}")
    print(f"输出文件: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
