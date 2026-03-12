import os
import binascii
from dataclasses import dataclass
import struct
from typing import Optional

import serial
import requests
import toml

config = toml.load("Config.toml")

url = config["Server"]["url"]
whole_len = config["Data"]["whole_len"]
data_len = config["Data"]["data_len"]
crc_len = config["Data"]["crc_len"]
tty = config["Serial"]["port"]


ser = serial.Serial(tty, baudrate=9600, timeout=None)


@dataclass
class Data:
    station_id: Optional[int] = None
    t: Optional[float] = None
    p: Optional[float] = None
    rh: Optional[float] = None
    error: Optional[Exception] = None

    def print(self):
        station_id = self.station_id
        t = self.t / 10
        p = self.p / 10
        rh = self.rh / 10
        print(f"{station_id=}\n{t=}\n{p=}\n{rh=}")

    def upload(self):
        if (self.station_id == 1):
            station_name = "AAU"
        else:
            station_name = "unknown"
        data = {
            "station_name": station_name,
            "temperature": self.t / 10,
            "pressure": self.p / 10,
            "relative_humidity": self.rh / 10,
        }
        try:
            response = requests.post(url, json=data)
            print(response.status_code)
            print(response.json())
        except Exception:
            print(data)
            print("等待服务器连接...")


def decode(raw_data: bytes):
    playload = raw_data[:data_len]
    remote_crc = struct.unpack(">I", raw_data[data_len:])[0]
    local_crc = binascii.crc32(playload)

    if remote_crc == local_crc:
        try:
            station_id, t, p, rh = struct.unpack(">Bhhh", playload)
            return Data(station_id, t, p, rh)
        except Exception as error:
            return Data(error=error)
    else:
        return Data(error="CRC校验失败，接收到错误数据")


# 读取一行数据
while True:
    response = ser.read(whole_len)
    print(response)
    if response.__len__() != whole_len:
        continue
    elif response.__len__() == whole_len:
        data = decode(response)

    if not data.error:
        # print(f"# {i}: {response}")
        # data.print()
        data.upload()

    if data.error:
        # print(f"# {i}: {data.error}")
        ser.reset_input_buffer()
        continue
