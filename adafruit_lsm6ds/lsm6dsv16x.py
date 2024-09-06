# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
# Modified by Cian Rodriguez for Dingo V2
# SPDX-License-Identifier: MIT
"""
This module provides the `adafruit_lsm6ds.LSM6DSV16X` subclass of LSM6DS sensors
==============================================================================
"""
import sys
import os
from adafruit_register.i2c_struct import ROUnaryStruct, Struct
from adafruit_register.i2c_bits import RWBits, ROBits
from adafruit_register.i2c_bit import RWBit, ROBit
from micropython import const
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from __init__ import LSM6DS, CV, _LSM6DS_EMB_FUNC_INIT_A, LSM6DS_DEFAULT_ADDRESS, _LSM6DS_EMB_FUNC_EN_A

_LSM6DSV16X_SFLP_ODR = const(0x5E)
_LSM6DSV16X_EMB_FUNC_FIFO_EN_A = const(0x44)
_LSM6DSV16X_FIFO_CTRL4 = const(0x0A)
_LSM6DSV16X_FIFO_STATUS1 = const(0x1B)
_LSM6DSV16X_FIFO_DATA_OUT_X_L = const(0x79)
_LSM6DSV16X_FIFO_DATA_OUT_TAG = const(0x78)

LSM6DSV16X_CHIP_ID = const(0x70)


class SFLPRate(CV):
    """Options for ``accelerometer_data_rate`` and ``gyro_data_rate``"""


class FIFOMode(CV):
    """Options for ``accelerometer_data_rate`` and ``gyro_data_rate``"""


@dataclass
class FIFOStatus:
    samples: int
    wtm: bool
    ovr: bool
    full: bool
    bdr: bool
    ovr_latch: bool


SFLPRate.add_values(
    (
        ("RATE_15_HZ", 0, 15.0, None),
        ("RATE_30_HZ", 1, 30.0, None),
        ("RATE_60_HZ", 2, 60.0, None),
        ("RATE_120_HZ", 3, 120.0, None),
        ("RATE_240_HZ", 4, 240.0, None),
        ("RATE_480_HZ", 5, 480.0, None),
    )
)

FIFOMode.add_values(
    (
        ("LSM6DSV16X_BYPASS_MODE", 0, 0, None),
        ("LSM6DSV16X_FIFO_MODE", 1, 21, None),
        ("LSM6DSV16X_CONTINUOUS_WTM_TO_FULL_MODE", 2, 2, None),
        ("LSM6DSV16X_CONTINUOUS_TO_FIFO_MODE", 3, 3, None),
        ("LSM6DSV16X_BYPASS_TO_CONTINUOUS_MODE", 4, 4, None),
        ("LSM6DSV16X_CONTINUOUS_MODE", 5, 5, None),
        ("LSM6DSV16X_BYPASS_TO_FIFO_MODE", 6, 6, None),
    )
)

try:
    import typing  # pylint: disable=unused-import
    from busio import I2C
except ImportError:
    pass


class LSM6DSV16X(LSM6DS):  # pylint: disable=too-many-instance-attributes

    """Driver for the LSM6DSV16X 6-axis accelerometer and gyroscope.

    :param ~busio.I2C i2c_bus: The I2C bus the LSM6DSV16X is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x6A`


    **Quickstart: Importing and using the device**

        Here is an example of using the :class:`LSM6DSV16X` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import board
            from adafruit_lsm6ds.LSM6DSV16X import LSM6DSV16X

        Once this is done you can define your `board.I2C` object and define your sensor object

        .. code-block:: python

            i2c = board.I2C()  # uses board.SCL and board.SDA
            sensor = LSM6DSV16X(i2c)

        Now you have access to the :attr:`acceleration` and :attr:`gyro`: attributes

        .. code-block:: python

            acc_x, acc_y, acc_z = sensor.acceleration
            gyro_x, gyro_z, gyro_z = sensor.gyro

    """

    CHIP_ID = LSM6DSV16X_CHIP_ID
    _sflp_data_rate = RWBits(3, _LSM6DSV16X_SFLP_ODR, 3)
    _sflp_batch = RWBit(_LSM6DSV16X_EMB_FUNC_FIFO_EN_A, 1)
    _fifo_mode = RWBits(3, _LSM6DSV16X_FIFO_CTRL4, 0)
    _sflp_init = RWBit(_LSM6DS_EMB_FUNC_INIT_A, 1)
    _fifo_status1 = ROBits(8, _LSM6DSV16X_FIFO_STATUS1, 0, 2)

    _fifo_data_out_tag = ROBits(5, _LSM6DSV16X_FIFO_DATA_OUT_TAG, 3)
    _raw_sensor_fusion_data = Struct(_LSM6DSV16X_FIFO_DATA_OUT_X_L, "<hhh")
    _sflp_en = RWBit(_LSM6DS_EMB_FUNC_EN_A, 1)

    SAMPLES_BITMASK = 0b0000000111111111
    WTM_BITMASK = 0b1000000000000000
    OVR_BITMASK = 0b0100000000000000
    FULL_BITMASK = 0b0010000000000000
    BDR_BITMASK = 0b0001000000000000
    OVR_LATCHED_BITMASK = 0b0000100000000000

    def __init__(
            self,
            i2c_bus: I2C,
            address: int = LSM6DS_DEFAULT_ADDRESS,
            ucf: str = None,
            sensor_fusion: bool = True
    ) -> None:
        super().__init__(i2c_bus, address, ucf)
        self._i3c_disable = True
        if sensor_fusion:
            self._enable_sflp()

    def _enable_sflp(self):
        self._mem_bank = 1  # Enable config reg for embedded funcs
        self._sflp_data_rate = SFLPRate.RATE_120_HZ  # Set rate
        self._sflp_batch = 1  # Set batching
        self._fifo_mode = FIFOMode.LSM6DSV16X_CONTINUOUS_MODE
        self._sflp_en = 1
        # self._sflp_init = 1
        self._mem_bank = 0

    @property
    def quaternion(self):
        status = self._read_status()
        num_samples = status.samples
        raw_quat_data = self._raw_sensor_fusion_data    # Check tag to see if it is quat data!
        # print(num_samples)
        # for i in range(num_samples):
        print("sample:", num_samples)
        print("tag:", self._fifo_data_out_tag)
        print("data:", raw_quat_data)


    def _read_status(self):
        raw_status = self._fifo_status1
        samples = raw_status & self.SAMPLES_BITMASK
        wtm = bool(raw_status & self.WTM_BITMASK)
        ovr = bool(raw_status & self.OVR_BITMASK)
        full = bool(raw_status & self.FULL_BITMASK)
        bdr = bool(raw_status & self.BDR_BITMASK)
        ovr_latch = bool(raw_status & self.OVR_LATCHED_BITMASK)
        return FIFOStatus(samples, wtm, ovr, full, bdr, ovr_latch)
