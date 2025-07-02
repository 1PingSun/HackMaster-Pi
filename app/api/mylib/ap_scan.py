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
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # 等待掃描完成
        time.sleep(scan_duration)
        
        # 停止掃描
        os.killpg(os.getpgid(process.pid), 15)
        process.wait()
        
        # 解析結果
        csv_file = temp_file + '-01.csv'
        networks = parse_csv_output(csv_file)
        
    except Exception as e:
        print(f"掃描錯誤: {e}")
    finally:
        # 清理
        if process:
            try:
                os.killpg(os.getpgid(process.pid), 15)
            except:
                pass
        
        cleanup_files(temp_file)
    
    return networks

def parse_csv_output(csv_file: str) -> List[Dict]:
    """解析 airodump-ng 的 CSV 輸出"""
    networks = []
    
    try:
        if not os.path.exists(csv_file):
            return networks
        
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 找到 AP 資料區段
        ap_data_started = False
        
        for line in lines:
            line = line.strip()
            
            # 跳過空行
            if not line:
                continue
            
            # 檢查是否為 AP 區段標題
            if 'BSSID' in line and 'ESSID' in line:
                ap_data_started = True
                continue
            
            # 遇到 Station 區段就停止
            if 'Station MAC' in line:
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
    
    except Exception as e:
        print(f"解析 CSV 錯誤: {e}")
    
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