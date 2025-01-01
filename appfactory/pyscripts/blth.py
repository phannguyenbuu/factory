import asyncio
from bleak import BleakClient
from bleak import BleakScanner

ADDRESS = "F8:60:46:0A:6B:28"  # Địa chỉ MAC của TTLock
UUID_WRITE = "000018F5-0000-1000-8000-00805F9B34FB"  # UUID dịch vụ cần gửi lệnh

async def send_command_to_ttlock():
    async with BleakClient(ADDRESS) as client:
        if client.is_connected:
            print("Connected to TTLock!")
            
            # Lệnh cần gửi (được mã hóa, ví dụ lệnh mở khóa)
            command = bytes.fromhex("01020304")  # Thay thế bằng lệnh cụ thể của bạn
            
            await client.write_gatt_char(UUID_WRITE, command)
            print("Command sent!")

# asyncio.run(send_command_to_ttlock())


async def find_device():
    devices = await BleakScanner.discover()
    for device in devices:
        print(f"Address: {device.address}, Name: {device.name}")

asyncio.run(find_device())

