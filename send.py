import binascii
import struct
import time

import serial
import toml

config = toml.load("Config.toml")

whole_len = config["Data"]["whole_len"]
data_len = config["Data"]["data_len"]
crc_len = config["Data"]["crc_len"]
tty = config["Serial"]["send_port"]

station_id = 1
t = 253      # 25.3
p = 10132    # 1013.2
rh = 563     # 56.3
interval = 1

ser = serial.Serial(tty, baudrate=9600, timeout=None)

while True:
    payload = struct.pack(">Bhhh", station_id, t, p, rh)
    local_crc = binascii.crc32(payload)
    crc = struct.pack(">I", local_crc)
    data = payload + crc
    print(data)

    if len(payload) != data_len:
        continue
    if len(crc) != crc_len:
        continue
    if len(data) != whole_len:
        continue

    ser.write(data)
    time.sleep(interval)
