# SPDX-FileCopyrightText: Copyright (c) 2022 Edrig
#
# SPDX-License-Identifier: MIT
import time
import board
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3

i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
sensor = LSM6DS3(i2c)

while True:
    print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (sensor.accelerometer))
    print("Gyro X:%.2f, Y: %.2f, Z: %.2f radians/s" % (sensor.gyroscope))
    print("")
    time.sleep(0.5)
