#!/bin/bash

# Bước 1: Cập nhật hệ thống và cài đặt Python (nếu chưa có)
echo "Cập nhật hệ thống và cài đặt Python..."
sudo apt update && sudo apt install -y python3 python3-venv python3-pip

# Bước 2: Tạo môi trường ảo nếu chưa có
if [ ! -d "venv" ]; then
    echo "Tạo môi trường ảo Python..."
    python3 -m venv venv
else
    echo "Môi trường ảo đã tồn tại. Bỏ qua bước tạo."
fi

# Bước 3: Kích hoạt môi trường ảo
echo "Kích hoạt môi trường ảo..."
source venv/bin/activate

# Bước 4: Cài đặt các gói Python cần thiết
echo "Cài đặt các gói Python..."
pip install --upgrade pip
pip install django djangorestframework celery colorama openpyxl pandas

# Bước 5: Tạo file requirements.txt
echo "Tạo file requirements.txt..."
pip freeze > requirements.txt

# Bước 6: Thông báo hoàn tất
echo "Hoàn tất cài đặt môi trường Python và các gói cần thiết."
# scp setup_env.sh root@145.223.23.137:factory