#!/bin/bash

# 顯示執行步驟訊息的函數
log() {
    echo -e "\e[1;34m[INFO]\e[0m $1"
}

error() {
    echo -e "\e[1;31m[ERROR]\e[0m $1"
}

success() {
    echo -e "\e[1;32m[SUCCESS]\e[0m $1"
}

# 獲取絕對路徑
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_DIR="$SCRIPT_DIR/../app"
ENV_DIR="$SCRIPT_DIR/../app/env"

# 檢查是否為 root 用戶
if [ "$EUID" -ne 0 ]; then
    error "請使用 sudo 執行此腳本"
    exit 1
fi

# 檢查 app 目錄是否存在
if [ ! -d "$APP_DIR" ]; then
    error "找不到應用程式目錄: $APP_DIR"
    exit 1
fi

# 檢查虛擬環境目錄是否存在
if [ ! -d "$ENV_DIR" ]; then
    error "找不到虛擬環境目錄: $ENV_DIR"
    log "正在創建虛擬環境..."
    python3 -m venv "$ENV_DIR"
    
    if [ ! -d "$ENV_DIR" ]; then
        error "無法創建虛擬環境。請手動創建並安裝依賴。"
        exit 1
    else
        success "虛擬環境創建成功"
    fi
fi

# 檢查 main.py 是否存在
if [ ! -f "$APP_DIR/main.py" ]; then
    error "找不到 $APP_DIR/main.py 檔案"
    exit 1
fi

# 為 main.py 添加執行權限
chmod +x "$APP_DIR/main.py"
success "已為 main.py 設置執行權限"

# 創建 systemd 服務檔案
SERVICE_FILE="/etc/systemd/system/hackmaster-pi.service"

log "正在創建 systemd 服務檔案..."
cat > "$SERVICE_FILE" << EOL
[Unit]
Description=HackMaster Pi Application
After=network.target

[Service]
ExecStart=/bin/bash -c 'cd ${APP_DIR} && sudo ${ENV_DIR}/bin/python3 main.py'
WorkingDirectory=${APP_DIR}
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# 重載 systemd 配置
log "正在重載 systemd 配置..."
systemctl daemon-reload

# 啟用服務
log "正在啟用 HackMaster Pi 服務..."
systemctl enable hackmaster-pi.service

# 啟動服務
log "正在啟動 HackMaster Pi 服務..."
systemctl start hackmaster-pi.service

# 檢查服務狀態
sleep 2
if systemctl is-active --quiet hackmaster-pi.service; then
    success "HackMaster Pi 服務已成功啟動！"
    log "您可以使用以下命令檢查服務狀態:"
    log "  sudo systemctl status hackmaster-pi.service"
else
    error "HackMaster Pi 服務啟動失敗。請檢查日誌:"
    log "  sudo systemctl status hackmaster-pi.service"
    log "  sudo journalctl -u hackmaster-pi.service"
fi

success "設置完成！Raspberry Pi 將在每次開機時自動執行應用程式。"