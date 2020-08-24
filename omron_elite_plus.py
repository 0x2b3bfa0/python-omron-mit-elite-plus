#!/usr/bin/env python3

import usb

from operator import xor
from functools import reduce
from dataclasses import dataclass
from datetime import datetime, timedelta
from elevate import elevate

class ElitePlus():
    """MIT Elite Plus HEM-7301-ITKE7 USB blood pressure meter 0590:0028."""
    @dataclass
    class Measurement:
        time: datetime
        systolic: int
        diastolic: int
        pulse: int

    def __init__(self, vendor=0x0590, product=0x0028, timeout=0.5):
        self.vendor, self.product, self.timeout = vendor, product, timeout
        self.device = self.detect(self.vendor, self.product)
        assert self.device
        self.connect()

    @staticmethod
    def detect(vendor, product):
        """Detects the device."""
        return usb.core.find(
            idProduct=product,
            idVendor=vendor
            )

    def connect(self):
        """Connects to the device."""
        if self.device.is_kernel_driver_active(0):
            self.device.detach_kernel_driver(0)
        self.device.set_configuration()
        #usb.util.claim_interface(device, None)

        request_type = usb.util.build_request_type(
            recipient=usb.util.CTRL_RECIPIENT_INTERFACE,
            type=usb.util.CTRL_TYPE_CLASS,
            direction=usb.util.CTRL_OUT
            )
        self.device.ctrl_transfer(
            timeout=int(1000 * self.timeout),
            bmRequestType=request_type,
            data_or_wLength=(0, 0),
            wValue=0x300,
            bRequest=9,
            wIndex=0
            )

    def read(self):
        """Reads data from the device."""
        data = bytes()
        while True:
            chunk = bytes(self.device.read(0x81, 8, int(1000 * self.timeout)))
            if not chunk or chunk[0] not in range(1, 8):
                return None
            data += chunk[1:chunk[0]+1]
            if chunk[0] < 7:
                break
        #assert reduce(xor, data[2:], 0) == 0
        if data[0:2] == b"OK":
            return data[2:-1]

    def write(self, *data):
        """Writes data to the device."""
        data = b"".join(data)
        assert len(data) < 256
        packet = bytes([len(data), *data])  # prepend packet length byte
        return self.device.write(0x02, packet, int(1000 * self.timeout))

    def command(self, *command):
        """Sends a command to the device and returns its output."""
        self.write(*command)
        return self.read()

    def wakeup(self):
        """Powers on the device."""
        try:
            response = self.read()
        except usb.core.USBError:
            pass
        for _ in range(10):
            self.write(7 * b'\x00')
            self.write(7 * b'\x00')
            try:
                response = self.read()
            except usb.core.USBError:
                pass
            else:
                if response:
                    self.active = True
                    break

    def shutdown(self):
        """Powers off the device."""
        self.active = False
        self.write(b"END00")

    def clock(self):
        """Retrieves the current date + time from the device clock."""
        year, month, day, hour, minute, second = self.command(b"GCL00")[1:7]
        return datetime(2000 + year, month, day, hour, minute, second)

    def clear(self):
        """Clears all the measurements stored on the device memory."""
        self.command(b"MCL00")

    def count(self):
        """Retrieves the number of measurements stored on the device memory."""
        return self.command(b"CNT00")[2]

    def measurements(self):
        """Retrieves all the measurements stored on the device memory."""
        offset = (datetime.now() - self.clock()).total_seconds()
        for index in range(self.count()):
            record = self.command(b"MES\x00\x00", bytes([index]) * 2)
            time = datetime(2000 + record[1], *record[2:7])
            systolic, diastolic, pulse = record[9:12]

            yield self.Measurement(
                time + timedelta(seconds=offset),
                systolic,
                diastolic,
                pulse
                )

    def __len__(self):
        return self.count()

    def __enter__(self):
        self.wakeup()
        return self

    def __exit__(self, *exception):
        self.shutdown()


if __name__ == "__main__":
    elevate()  # Run as superuser
    with ElitePlus() as meter:
        for measurement in meter.measurements():
            print(",".join([
                str(measurement.time.replace(microsecond=0).isoformat().replace("T", " ")),
                str(measurement.systolic),
                str(measurement.diastolic),
                str(measurement.pulse)
                ]))
        meter.clear()

