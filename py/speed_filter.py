import os
import re
import time
import requests
import concurrent.futures
import sys
import random

# ===============================
# 1. 配置区
# ===============================
INPUT_FILES = ["py/live.txt", "py/IPTV2.txt"]
OUTPUT_FILE = "py/livezubo.txt"
BLACKLIST_FILE = "py/blacklist.txt"

# 测速参数
CHECK_COUNT = 3          # 每个服务器随机抽测 3 个频道
MIN_PEAK_REQUIRED = 1.0  # 理想达标门槛 (MB/s)
BACKUP_COUNT = 8         # 降级保底数量：如果达标不足，强制保留前 8 名最快服务器
TIMEOUT = 8              # 单个频道请求超时时间

def get_realtime_speed(url):
    """
    核心测速函数：通过模拟播放器请求并读取 1MB 数据来计算真实速度
    """
    try:
        start_time = time.time()
        # 模拟播放器 User-Agent
        headers = {'User-Agent': 'vlc/3.0.8'}
        # stream=True 必选，否则会下载整个文件导致超时
        r = requests.get(url, timeout=TIMEOUT, stream=True, headers=headers)
        
        if r.status_code == 200:
            content = b""
            # 持续读取数据直到满 1MB 或超过 6 秒
            for chunk in r.iter_content(chunk_size=1024 * 256):
                content += chunk
                if len(content) >= 1024 * 1024 or (time.time() - start_time) > 6:
                    break
            
            duration = time.time() - start_time
            # 计算速度: MB / 秒
            speed = (len(content) / 1024 / 1024) / duration if duration > 0 else 0
            return speed
    except Exception:
        pass
    return 0.0

def load_blacklist():
    """加载已存在的黑名单 IP:PORT"""
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            # 去重并去除空白符
            return set(line.strip() for line in f if line.strip())
    return set()

def save_to_blacklist(ip):
    """将死 IP 实时追加到黑名单文件"""
    try:
        with open(BLACKLIST_FILE, "a", encoding="utf-8") as f:
            f.write(f"{ip}\n")
    except Exception as e:
        print(f"写入黑名单失败: {e}")

def test_ip_group(ip_port, channels):
    """
    对单个 IP 服务器进行组测
    """
    all_urls = [url for _, url in channels]
    if not all_urls:
        return ip_port, 0.0, False
    
    # 随机抽取样本进行测试，增加覆盖率
    test_targets = random.sample(all_urls, min(len(all_urls), CHECK_COUNT))
    max_speed = 0.0
    
    for url in test_targets:
        speed = get_realtime_speed(url)
        if speed > max_speed:
            max_speed = speed

    timestamp = time.strftime("%H:%M:%S", time.localtime())
    status = "SUCCESS" if max_speed > 0.01 else "DEAD"
    
    # 强制刷新输出，确保 GitHub Actions 日志实时显示
    print(f"[{timestamp}] {ip_port:21} | {status:7} | 速度: {max_speed:.2f} MB/s", flush=True)
    
    return ip_port, max_speed, (max_speed > 0.01)

def main():
    print(f"🎬 脚本启动... [保底模式: {BACKUP_COUNT}]")
    
    # 1. 加载黑名单
    blacklist = load_blacklist()
    print(f"🚫 已加载黑名单 IP 数: {len(blacklist)}")
    
    # 2. 读取输入文件
    all_lines = []
    for input_file in INPUT_FILES:
        if os.path.exists(input_file):
            with open(input_file, "r", encoding="utf-8") as f:
                all_lines.extend(f.readlines())
        else:
            print(f"⚠️ 找不到输入文件: {input_file}")

    # 3. 解析并过滤黑名单
    ip_groups = {}
    for line in all_lines:
        line = line.strip()
        if "," in line and "http://" in line:
            name, url = line.split(",", 1)
            # 提取 http://xxxx:port/ 中的 xxxx:port
            match = re.search(r'http://(.*?)/', url)
            if match:
                ip_port = match.group(1)
                if ip_port in blacklist:
                    continue
                ip_groups.setdefault(ip_port, []).append((name, url))

    if not ip_groups:
        print("❌ 没有剩余可测试的服务器。")
        return

    print(f"🚀 开始并发测试 {len(ip_groups)} 个服务器...")
    all_results = []
    
    # 4. 并发测速 (保持 max_workers=5 避免被酒店源封禁 IP)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_ip_group, ip, chs): ip for ip, chs in ip_groups.items()}
        for future in concurrent.futures.as_completed(futures):
            ip, speed, is_alive = future.result()
            if is_alive:
                all_results.append({'ip': ip, 'speed': speed})
            else:
                # 实时存入黑名单
                save_to_blacklist(ip)

    # 5. 筛选与保底方案
    # 首先选出真正达标的
    final_list = [item for item in all_results if item['speed'] >= MIN_PEAK_REQUIRED]
    
    # 如果达标数太少，则按速度排序取前 N 名
    if len(final_list) < BACKUP_COUNT:
        print(f"⚠️ 达标服务器不足 ({len(final_list)}/{BACKUP_COUNT})，执行降级保底逻辑...")
        all_results.sort(key=lambda x: x['speed'], reverse=True)
        final_list = all_results[:BACKUP_COUNT]

    # 6. 生成输出文件
    count = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in final_list:
            ip = item['ip']
            speed = item['speed']
            for name, url in ip_groups[ip]:
                # 在频道名后标注实测速度，方便调试
                f.write(f"{name}({speed:.2f}MB),{url}\n")
                count += 1
                
    print(f"--- 处理完成 ---")
    print(f"✅ 选定服务器: {len(final_list)} 个")
    print(f"✅ 生成线路数: {count} 条")
    print(f"📝 结果已保存至: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
