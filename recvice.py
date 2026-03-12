import binascii
import struct
from dataclasses import dataclass
from typing import Optional

import serial
import requests
import toml

config = toml.load("Config.toml")

URL = config["Server"]["url"]
WHOLE_LEN = config["Data"]["whole_len"]
DATA_LEN = config["Data"]["data_len"]
_CRC_LEN = config["Data"]["crc_len"]  # Kept for config compatibility.
TTY = config["Serial"]["revice_port"]
SCALE = 10


ser = serial.Serial(TTY, baudrate=9600, timeout=None)


@dataclass
class Data:
    station_id: Optional[int] = None
    t: Optional[float] = None
    p: Optional[float] = None
    rh: Optional[float] = None
    error: Optional[object] = None

    def _scaled_values(self) -> tuple[float, float, float]:
        return self.t / SCALE, self.p / SCALE, self.rh / SCALE

    def print(self):
        station_id = self.station_id
        t, p, rh = self._scaled_values()
        print(f"{station_id=}\n{t=}\n{p=}\n{rh=}")

    def upload(self):
        station_name = "AAU" if self.station_id == 1 else "unknown"
        t, p, rh = self._scaled_values()
        data = {
            "station_name": station_name,
            "temperature": t,
            "pressure": p,
            "relative_humidity": rh,
        }
        try:
            response = requests.post(URL, json=data)
            print(response.status_code)
            print(response.json())
        except Exception:
            print(data)
            print("等待服务器连接...")


def decode(raw_data: bytes) -> Data:
    payload = raw_data[:DATA_LEN]
    remote_crc = struct.unpack(">I", raw_data[DATA_LEN:])[0]
    local_crc = binascii.crc32(payload)

    if remote_crc == local_crc:
        try:
            station_id, t, p, rh = struct.unpack(">Bhhh", payload)
            return Data(station_id, t, p, rh)
        except Exception as error:
            return Data(error=error)
    return Data(error="CRC校验失败，接收到错误数据")


# 读取一行数据
while True:
    response = ser.read(WHOLE_LEN)
    print(response)
    if len(response) != WHOLE_LEN:
        continue
    data = decode(response)

    if not data.error:
        # print(f"# {i}: {response}")
        # data.print()
        data.upload()

    if data.error:
        # print(f"# {i}: {data.error}")
        ser.reset_input_buffer()
