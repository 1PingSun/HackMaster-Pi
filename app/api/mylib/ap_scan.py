import subprocess
import tempfile
import os
import time
from typing import List, Dict

def scan_wifi_networks(interface: str = "wlan0", scan_duration: int = 10) -> List[Dict]:
    """
    執行一次 WiFi 掃描並返回結果
    
    Args:
        interface: 網路介面名稱 (預設: wlan0)
        scan_duration: 掃描持續時間(秒) (預設: 10秒)
    
    Returns:
        List[Dict]: 包含 BSSID, CH, ENC, ESSID 的字典清單
    """
    networks = []
    temp_file = None
    process = None
    
    try:
        # 創建臨時檔案
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        # 執行 airodump-ng
        cmd = [
            'sudo', 'airodump-ng',
            '--write', temp_file,
            '--write-interval', '1',
            '--output-format', 'csv',
            interface
        ]
        
        # 啟動掃描
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待掃描完成
        time.sleep(scan_duration)
        
        # 停止掃描
        try:
            process.terminate()
            # 給進程足夠的時間來正確關閉和寫入文件
            process.wait(timeout=10)  # 增加到 10 秒
        except subprocess.TimeoutExpired:
            print("進程未在 10 秒內正常終止，強制結束")
            process.kill()
            process.wait()
        
        # 給文件系統一點時間確保文件完全寫入
        time.sleep(1)
        
        # 解析結果
        csv_file = temp_file + '-01.csv'
        networks = parse_csv_output(csv_file)
        
    except Exception as e:
        print(f"掃描錯誤: {e}")
    finally:
        # 清理
        if process:
            try:
                if process.poll() is None:  # 進程仍在運行
                    process.terminate()
                    try:
                        process.wait(timeout=10)  # 增加到 10 秒
                    except subprocess.TimeoutExpired:
                        print("清理時進程未正常終止，強制結束")
                        process.kill()
                        process.wait()
            except Exception as cleanup_error:
                print(f"清理進程時發生錯誤: {cleanup_error}")
        
        cleanup_files(temp_file)
    
    return networks

def parse_csv_output(csv_file: str) -> List[Dict]:
    """解析 airodump-ng 的 CSV 輸出"""
    networks = []
    
    try:
        if not os.path.exists(csv_file):
            print(f"CSV 文件不存在: {csv_file}")
            return networks
        
        # 檢查文件大小
        file_size = os.path.getsize(csv_file)
        print(f"CSV 文件大小: {file_size} bytes")
        
        if file_size == 0:
            print("CSV 文件為空")
            return networks
        
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        print(f"CSV 文件共有 {len(lines)} 行")
        
        # 找到 AP 資料區段
        ap_data_started = False
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # 跳過空行
            if not line:
                continue
            
            # 檢查是否為 AP 區段標題
            if 'BSSID' in line and 'ESSID' in line:
                print(f"找到 AP 資料標題在第 {line_num + 1} 行")
                ap_data_started = True
                continue
            
            # 遇到 Station 區段就停止
            if 'Station MAC' in line:
                print(f"遇到 Station 區段在第 {line_num + 1} 行，停止解析")
                break
            
            # 解析 AP 資料
            if ap_data_started:
                parts = line.split(',')
                
                if len(parts) >= 14:
                    bssid = parts[0].strip()
                    channel = parts[3].strip()
                    privacy = parts[5].strip()
                    essid = parts[13].strip() if len(parts) > 13 else ''
                    
                    # 檢查是否為有效的 BSSID
                    if ':' in bssid and len(bssid) == 17:
                        network = {
                            'BSSID': bssid,
                            'CH': channel,
                            'ENC': privacy,
                            'ESSID': essid
                        }
                        networks.append(network)
                        print(f"解析到網路: {bssid} - {essid}")
        
        print(f"總共解析到 {len(networks)} 個網路")
    
    except Exception as e:
        print(f"解析 CSV 錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    return networks

def cleanup_files(temp_file: str):
    """清理臨時檔案"""
    if temp_file:
        suffixes = ['-01.csv', '-01.cap', '-01.kismet.csv', '-01.log.csv', '']
        for suffix in suffixes:
            try:
                file_path = temp_file + suffix
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

# 使用範例
if __name__ == "__main__":
    print("執行 WiFi 掃描...")
    
    # 執行掃描
    networks = scan_wifi_networks("wlan0", 15)
    
    # 顯示結果
    print(f"發現 {len(networks)} 個網路:")
    for i, network in enumerate(networks, 1):
        print(f"{i:2d}. BSSID: {network['BSSID']} | "
              f"CH: {network['CH']:2s} | "
              f"ENC: {network['ENC']:8s} | "
              f"ESSID: '{network['ESSID']}'")