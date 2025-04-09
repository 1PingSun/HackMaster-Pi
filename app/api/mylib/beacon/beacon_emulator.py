#!/usr/bin/env python3
import subprocess
import time
import threading
import os

# 全局變量來追踪廣播狀態
broadcasting_thread = None
stop_event = threading.Event()

def start_ibeacon(uuid="AA 21 98 B2 46 30 11 EE BE 56 02 42 AC 12 00 02", 
                  major="00 01", 
                  minor="00 02", 
                  power="C8"):
    """
    開始 iBeacon 廣播
    
    參數:
        uuid: iBeacon UUID (空格分隔的十六進制字符串)
        major: iBeacon Major 值 (空格分隔的十六進制字符串)
        minor: iBeacon Minor 值 (空格分隔的十六進制字符串)
        power: 發射功率校準值 (十六進制字符串)
        
    返回:
        成功返回 True，失敗返回 False
    """
    global broadcasting_thread, stop_event
    
    # 如果已經在廣播，先停止
    if broadcasting_thread and broadcasting_thread.is_alive():
        stop_ibeacon()
    
    # 重置停止事件
    stop_event.clear()
    
    try:
        # 重置藍牙設備
        subprocess.run(["sudo", "hciconfig", "hci0", "down"], check=True)
        subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)
        
        # 設置為廣播模式
        subprocess.run(["sudo", "hciconfig", "hci0", "leadv", "3"], check=True)
        
        # 創建廣播線程
        def broadcast_loop():
            while not stop_event.is_set():
                cmd = ["sudo", "hcitool", "-i", "hci0", "cmd", "0x08", "0x0008", 
                      "1E", "02", "01", "06", "1A", "FF", "4C", "00", "02", "15"] + uuid.split() + major.split() + minor.split() + [power]
                try:
                    subprocess.run(cmd, check=True)
                except subprocess.SubprocessError:
                    if not stop_event.is_set():  # 只有當不是因為停止事件才輸出錯誤
                        print("廣播命令執行失敗")
                time.sleep(1)  # 每秒發送一次
        
        # 啟動廣播線程
        broadcasting_thread = threading.Thread(target=broadcast_loop)
        broadcasting_thread.daemon = True  # 設為守護線程，主程序結束時自動終止
        broadcasting_thread.start()
        
        print(f"開始廣播 iBeacon: UUID={uuid}, Major={major}, Minor={minor}")
        return True
        
    except Exception as e:
        print(f"啟動 iBeacon 廣播時出錯: {e}")
        # 嘗試清理
        try:
            subprocess.run(["sudo", "hciconfig", "hci0", "reset"], check=False)
        except:
            pass
        return False

def stop_ibeacon():
    """
    停止 iBeacon 廣播
    
    返回:
        成功返回 True，失敗返回 False
    """
    global broadcasting_thread, stop_event
    
    try:
        # 設置停止事件
        stop_event.set()
        
        # 等待廣播線程結束（最多等待 3 秒）
        if broadcasting_thread and broadcasting_thread.is_alive():
            broadcasting_thread.join(timeout=3)
        
        # 停止廣播
        subprocess.run(["sudo", "hciconfig", "hci0", "noleadv"], check=False)
        # 重置藍牙設備
        subprocess.run(["sudo", "hciconfig", "hci0", "reset"], check=True)
        
        print("iBeacon 廣播已停止")
        return True
        
    except Exception as e:
        print(f"停止 iBeacon 廣播時出錯: {e}")
        return False

# 測試代碼
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        # 可以指定自定義參數
        if len(sys.argv) > 2:
            start_ibeacon(uuid=sys.argv[2])
        else:
            start_ibeacon()
        input("按 Enter 鍵停止廣播...")
        stop_ibeacon()
    elif len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_ibeacon()
    else:
        print("用法: python3 ibeacon.py [start|stop] [optional_uuid]")