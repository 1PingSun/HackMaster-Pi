#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import subprocess
import re
import time
from typing import List, Dict, Any, Optional

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BeaconScanner")

class BeaconScanner:
    """
    使用 BlueZ 掃描附近的 BLE Beacon
    """
    
    def __init__(self, scan_duration: int = 5, device_id: int = 0):
        """
        初始化 BeaconScanner

        Args:
            scan_duration: 掃描持續時間（秒）
            device_id: 藍牙介面 ID（hci0 為 0）
        """
        self.scan_duration = scan_duration
        self.device_id = device_id
        self.is_scanning = False
        self._last_scan_result = []

    async def scan(self) -> List[Dict[str, Any]]:
        """
        執行藍牙掃描，尋找附近的 Beacon 設備

        Returns:
            List[Dict[str, Any]]: 找到的 Beacon 列表
        """
        if self.is_scanning:
            logger.info("已有掃描進行中，返回上次結果")
            return self._last_scan_result
        
        self.is_scanning = True
        try:
            # 啟動 hcitool 掃描
            logger.info(f"開始掃描 BLE 裝置，持續 {self.scan_duration} 秒")
            
            # 使用 hcitool 掃描 BLE 設備
            cmd = [
                "sudo", "timeout", str(self.scan_duration),
                "hcitool", "-i", f"hci{self.device_id}", "lescan", "--duplicate"
            ]
            
            # 使用 tee 將輸出同時導向標準輸出和文件
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 同時啟動另一個進程來捕獲 hcidump 數據
            dump_cmd = [
                "sudo", "hcidump", "-i", f"hci{self.device_id}", "--raw"
            ]
            
            dump_process = subprocess.Popen(
                dump_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待掃描完成
            await asyncio.sleep(self.scan_duration + 1)
            
            # 強制終止進程
            process.terminate()
            dump_process.terminate()
            
            # 獲取 hcitool 輸出
            stdout, stderr = process.communicate()
            dump_stdout, dump_stderr = dump_process.communicate()
            
            # 解析 hcitool 輸出獲取設備列表
            devices = self._parse_lescan_output(stdout)
            
            # 解析 hcidump 輸出以獲取更多廣告數據（如UUID）
            beacon_data = self._parse_hcidump_output(dump_stdout)
            
            # 合併數據
            result = self._merge_device_data(devices, beacon_data)
            
            # 過濾，只保留可能是 Beacon 的設備
            beacons = self._filter_beacons(result)
            
            self._last_scan_result = beacons
            return beacons
            
        except Exception as e:
            logger.error(f"掃描時發生錯誤: {str(e)}")
            return []
        finally:
            self.is_scanning = False
    
    def _parse_lescan_output(self, output: str) -> List[Dict[str, Any]]:
        """解析 hcitool lescan 的輸出"""
        devices = []
        lines = output.strip().split('\n')
        
        # 第一行是標題，跳過
        for line in lines[1:]:
            parts = line.strip().split(' ', 1)
            if len(parts) >= 2:
                mac_address = parts[0]
                name = parts[1] if len(parts) > 1 else "Unknown"
                
                devices.append({
                    "mac_address": mac_address,
                    "name": name,
                    "rssi": -90  # 默認值，將從 hcidump 更新
                })
        
        return devices
    
    def _parse_hcidump_output(self, output: str) -> Dict[str, Dict[str, Any]]:
        """解析 hcidump 的輸出獲取更多設備信息"""
        devices_data = {}
        current_mac = None
        
        # 正則表達式匹配 MAC 地址
        mac_pattern = re.compile(r'> ([0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2})')
        
        # 匹配 RSSI 值
        rssi_pattern = re.compile(r'RSSI: (-\d+)')
        
        # 匹配 UUID
        uuid_pattern = re.compile(r'([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})')
        
        lines = output.strip().split('\n')
        
        for line in lines:
            # 尋找 MAC 地址
            mac_match = mac_pattern.search(line)
            if mac_match:
                current_mac = mac_match.group(1).lower()
                if current_mac not in devices_data:
                    devices_data[current_mac] = {}
                continue
            
            # 如果找到當前設備，尋找 RSSI
            if current_mac:
                rssi_match = rssi_pattern.search(line)
                if rssi_match:
                    devices_data[current_mac]["rssi"] = int(rssi_match.group(1))
                
                # 尋找 UUID
                uuid_match = uuid_pattern.search(line)
                if uuid_match:
                    devices_data[current_mac]["uuid"] = uuid_match.group(1)
        
        return devices_data
    
    def _merge_device_data(self, devices: List[Dict[str, Any]], beacon_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合併從不同來源獲取的設備數據"""
        merged_devices = []
        
        for device in devices:
            mac = device["mac_address"].lower()
            if mac in beacon_data:
                # 更新 RSSI
                if "rssi" in beacon_data[mac]:
                    device["rssi"] = beacon_data[mac]["rssi"]
                
                # 添加 UUID
                if "uuid" in beacon_data[mac]:
                    device["uuid"] = beacon_data[mac]["uuid"]
            
            merged_devices.append(device)
        
        return merged_devices
    
    def _filter_beacons(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """過濾設備列表，只保留 Beacon"""
        beacons = []
        
        for device in devices:
            # 簡單過濾：包含 UUID 的設備很可能是 Beacon
            if "uuid" in device:
                beacons.append(device)
                continue
            
            # 設備名稱含有 "beacon" 或其他相關關鍵詞
            name = device.get("name", "").lower()
            if any(keyword in name for keyword in ["beacon", "ibeacon", "tag", "ble"]):
                beacons.append(device)
                continue
        
        return beacons

    @staticmethod
    async def use_hexway_tool() -> List[Dict[str, Any]]:
        """
        使用 hexway/apple_bleee 工具掃描 AirPods 和其他 Apple 設備

        Returns:
            List[Dict[str, Any]]: 找到的 Beacon 列表
        """
        try:
            # 使用 subprocess 執行 apple_bleee 的 adv_airpods.py 腳本
            cmd = ["sudo", "python3", "/path/to/apple_bleee/adv_airpods.py", "--scan", "--timeout", "5"]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"執行 hexway 工具失敗: {stderr}")
                return []
            
            # 解析輸出
            beacons = []
            lines = stdout.strip().split('\n')
            
            for line in lines:
                # 嘗試解析 JSON 輸出
                try:
                    if line.startswith('{'):
                        data = json.loads(line)
                        if 'mac' in data and 'device' in data:
                            beacon = {
                                "mac_address": data["mac"],
                                "name": data.get("device", "Apple Device"),
                                "rssi": data.get("rssi", -90),
                                "uuid": f"Apple-{data.get('device_type', 'Unknown')}-{data['mac']}"
                            }
                            beacons.append(beacon)
                except json.JSONDecodeError:
                    pass
            
            return beacons
            
        except Exception as e:
            logger.error(f"使用 hexway 工具時發生錯誤: {str(e)}")
            return []

    @staticmethod
    async def get_combined_beacons(use_hexway: bool = True) -> List[Dict[str, Any]]:
        """
        同時使用多種方法獲取附近的 Beacon，並合併結果

        Args:
            use_hexway: 是否也使用 hexway/apple_bleee 工具

        Returns:
            List[Dict[str, Any]]: 合併後的 Beacon 列表
        """
        scanner = BeaconScanner()
        beacons = await scanner.scan()
        
        if use_hexway:
            apple_beacons = await BeaconScanner.use_hexway_tool()
            
            # 合併結果，避免重複
            existing_macs = {b["mac_address"] for b in beacons}
            for apple_beacon in apple_beacons:
                if apple_beacon["mac_address"] not in existing_macs:
                    beacons.append(apple_beacon)
        
        return beacons


async def main():
    """測試函數"""
    scanner = BeaconScanner()
    print("開始掃描附近的 Beacon...")
    
    beacons = await scanner.scan()
    
    print(f"找到 {len(beacons)} 個 Beacon:")
    for i, beacon in enumerate(beacons, 1):
        print(f"{i}. MAC: {beacon.get('mac_address')}")
        print(f"   名稱: {beacon.get('name', 'Unknown')}")
        print(f"   RSSI: {beacon.get('rssi', 'Unknown')} dBm")
        print(f"   UUID: {beacon.get('uuid', 'Unknown')}")
        print("---")


if __name__ == "__main__":
    # 直接執行此文件時運行測試函數
    asyncio.run(main())