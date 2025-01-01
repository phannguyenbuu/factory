import requests
import hashlib
import time
import urllib.parse

client_id = "4ea1ae2aefe24d6baac1d7447e2865e2"
client_secret = "f75fc703b879795e2a5c310ba915337a"
password = "00Silent"
password_md5 = hashlib.md5(password.encode()).hexdigest() #50b2d9be3ab9f3fba54e5b0b36cab20f
base_url = "https://cnapi.ttlock.com"
username = 'phannguyenbuu@gmail.com'
# token = '74e1361766a651a1f8657dfa35e5add7'


def connect():
    # Đặt thông tin clientId, clientSecret, password và thời gian
    
    # print(password_md5)
    current_millis = int(time.time() * 1000)  # Lấy thời gian hiện tại tính bằng mili giây

    # Mã hóa các tham số URL
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'username':'phannguyenbuu@gmail.com',
        'password': password_md5,  # Gửi mật khẩu MD5
        'date': current_millis
    }

    # Mã hóa URL
    encoded_params = urllib.parse.urlencode(params)
    # url = f"https://cnapi.ttlock.com/oauth2/token"
    url = "https://cnapi.ttlock.com/v3/lock/list?page=1&page_size=10"

    # Gửi yêu cầu POST
    response = requests.post(url, headers={
            'Authorization':
                'Bearer 74e1361766a651a1f8657dfa35e5add7'
            }, params=params)

    # Kiểm tra và in kết quả
    if response.status_code == 200:
        print("Request was successful.")
        print(response.json())  # In kết quả JSON từ API
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)

import requests
from datetime import datetime, timedelta

def get_lock_list(client_id, access_token):
    # URL API của TTLock
    current_time = datetime.now() + timedelta(minutes=5)
    timestamp = int(current_time.timestamp() * 1000)  # Chuyển thành mili-giây

    # URL API của TTLock
    url = f"{base_url}/v3/lock/list"
    
    # Các tham số gửi trong yêu cầu
    params = {
        'clientId': client_id,
        'accessToken': access_token,
        'pageNo': 1,
        'pageSize': 10,
        'date': timestamp,
    }

    # Gửi yêu cầu POST với Authorization header
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    try:
        # Gửi yêu cầu POST
        response = requests.post(url, headers=headers, params=params, verify=False)

        # Kiểm tra mã trạng thái HTTP
        if response.status_code == 200:
            # Nếu yêu cầu thành công, trả về dữ liệu từ API
            return response.json()
        else:
            # Nếu có lỗi, trả về mã lỗi và lý do
            return {"error": response.status_code, "message": response.text}
    except requests.exceptions.RequestException as e:
        # Bắt các lỗi kết nối và in ra lỗi
        return {"error": str(e)}

import requests

def auth(client_id, client_secret, username, password):
    url = f"{base_url}/oauth2/token"
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'username': username,
        'password': password,
    }

    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()  # Return response as a dictionary
    else:
        raise Exception('Failed to authenticate')



# Thử gọi hàm với các tham số
# client_id = "4ea1ae2aefe24d6baac1d7447e2865e2"
# access_token = "74e1361766a651a1f8657dfa35e5add7"
# page_no = 1
# page_size = 10
# date = 1637254867000  # Thời gian hiện tại hoặc một giá trị khác

# # Gọi hàm
# lock_list_response = get_lock_list(client_id, access_token, page_no, page_size, date)

# # In ra kết quả
# print(lock_list_response)
    


if __name__ == "__main__":
    try:
        token_response = auth(client_id, client_secret, username, password_md5)
        print("Authentication successful!")
        print("Response:", token_response['access_token'])

        token = token_response['access_token']

        locks = get_lock_list(client_id, token)['list']
        print(locks)
    except Exception as e:
        print("Error:", str(e))
