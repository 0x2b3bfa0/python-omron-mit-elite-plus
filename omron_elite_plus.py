#!/usr/bin/env python3
"""omron_elite_plus.py
Script for connecting to Omron blood pressure monitors over USB.

Originally based on
https://usb2me.wordpress.com/2013/02/06/omron-mit-elite-plus-hem-7301-itke7

Modified and added to by Helio Machado and Jotham Gates
"""
import usb
from dataclasses import dataclass
from datetime import datetime, timedelta
import argparse
import errno
import sys


class BPMNotFoundError(Exception):
    ...


DATETIME_FORMAT = "%Y-%d-%m %H:%M:%S"


class ElitePlus:
    """MIT Elite Plus HEM-7301-ITKE7 USB blood pressure meter 0590:0028."""

    @dataclass
    class Measurement:
        time: datetime
        systolic: int
        diastolic: int
        pulse: int

    def __init__(self, vendor=0x0590, product=0x0028, timeout=4):
        """Initialises the device connection.
        Clearing may need a larger timeout compared to other options from
        experience.
        """
        self.vendor, self.product, self.timeout = vendor, product, timeout
        self.device = self.detect(self.vendor, self.product)
        if not self.device:
            raise BPMNotFoundError(
                f"Blood pressure monitor with USB vendor id '{vendor:>04x}' and product id '{product:>04x}' not found."
            )
        self.connect()

    @staticmethod
    def detect(vendor, product):
        """Detects the device."""
        return usb.core.find(idProduct=product, idVendor=vendor)

    def connect(self):
        """Connects to the device."""
        if self.device.is_kernel_driver_active(0):
            self.device.detach_kernel_driver(0)
        self.device.set_configuration()
        # usb.util.claim_interface(device, None)

        request_type = usb.util.build_request_type(
            recipient=usb.util.CTRL_RECIPIENT_INTERFACE,
            type=usb.util.CTRL_TYPE_CLASS,
            direction=usb.util.CTRL_OUT,
        )

        self.device.ctrl_transfer(
            timeout=int(1000 * self.timeout),
            bmRequestType=request_type,
            data_or_wLength=(0, 0),
            wValue=0x300,
            bRequest=9,
            wIndex=0,
        )

    def read(self):
        """Reads data from the device."""
        data = bytes()
        while True:
            chunk = bytes(self.device.read(0x81, 8, int(1000 * self.timeout)))
            if not chunk or chunk[0] not in range(1, 8):
                return None
            data += chunk[1 : chunk[0] + 1]
            if chunk[0] < 7:
                break
        # assert reduce(xor, data[2:], 0) == 0
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
            self.write(7 * b"\x00")
            self.write(7 * b"\x00")
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

    def measurements(self, correct_time: bool = True):
        """Retrieves all the measurements stored on the device memory.
        If correct_time is true, an offset of the computer's time minus the
        monitor's time will be applied to each record to correct for the clock
        not being set correctly."""
        if correct_time:
            # Calculate the time offset to apply if needed.
            offset = (datetime.now() - self.clock()).total_seconds()

        for index in range(self.count()):
            # Get each record
            record = self.command(b"MES\x00\x00", bytes([index]) * 2)
            try:
                time = datetime(2000 + record[1], *record[2:7])
            except ValueError:
                # Time isn't known / formatted correctly, leave out.
                time = None

            systolic, diastolic, pulse = record[9:12]
            record = self.Measurement(time, systolic, diastolic, pulse)

            if correct_time and time:
                """Correct the time on the monitor with the computer's own
                time offset if needed."""
                record.time += timedelta(seconds=offset)

            yield record

    def __len__(self):
        return self.count()

    def __enter__(self):
        self.wakeup()
        return self

    def __exit__(self, *exception):
        self.shutdown()


def main(settings: argparse.Namespace):
    """Attempts to open the device and perform the required actions."""
    try:
        with ElitePlus() as meter:
            if settings.time:
                # Request the current time from the monitor.
                print("Monitor's inbuilt clock")
                print(meter.clock())

            if settings.number:
                # Request the number of records stored.
                print("Number of records on device")
                print(meter.count())

            if settings.read:
                # Request all measurements from the monitor.
                print("Date,Systolic,Diastolic,Pulse")
                for measurement in meter.measurements(settings.correct_times):
                    print(
                        ",".join(
                            [
                                str(
                                    measurement.time.strftime(DATETIME_FORMAT)
                                    if measurement.time
                                    else ""
                                ),
                                str(measurement.systolic),
                                str(measurement.diastolic),
                                str(measurement.pulse),
                            ]
                        )
                    )

            if settings.clear:
                # Request that the monitor delete its internal data.
                print("Requesting to clear internal data")
                meter.clear()

    except BPMNotFoundError as e:
        print(e, file=sys.stderr)


def parse_args() -> argparse.Namespace:
    """Parser for command line arguments and help text."""
    parser = argparse.ArgumentParser(
        description="Tool for connecting to Omron branded blood pressure monitors"
    )
    parser.add_argument(
        "-r", "--read", help="Read all data stored on the monitor.", action="store_true"
    )
    parser.add_argument(
        "--correct-times",
        help="When reading, adds an offset from the computer's time to the monitor's time for each record to correct for the date and time on the monitor not being set correctly.",
        action="store_true",
    )
    parser.add_argument(
        "-c",
        "--clear",
        help="Request that the monitor clear its internal memory after reading.",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--time",
        help="Get the current time from the monitor.",
        action="store_true",
    )
    parser.add_argument(
        "-n",
        "--number",
        help="Get the number of records stored on the monitor.",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write the results to the provided file instead of to the console.",
        type=str,
    )

    return parser.parse_args()


def run_as_users():
    """Attempts to run and connect as the current user. If this fails due to
    permissions, then attempts to run as root."""
    try:
        # Attempt to run as the current user.
        main(args)
    except usb.core.USBError as e:
        if e.errno == errno.EACCES:
            # Running as the current user failed. Attempt to run as the root user.
            print("Could not open the USB connection as:", file=sys.stderr)
            print(f"    {e}", file=sys.stderr)
            print("Will try to run as root.", file=sys.stderr)

            # Only import now as not needed if permissions are otherwise ok
            import elevate

            elevate.elevate()

            main(args)
        else:
            # Some other error that we don't know how to deal with.
            raise e


if __name__ == "__main__":
    args = parse_args()
    # print(args)
    if args.output:
        # Output file provided.
        try:
            with open(args.output, "w") as out_file:
                sys.stdout = out_file
                run_as_users()
        except OSError as e:
            print(f"Could not open output file '{args.output}' as:", file=sys.stderr)
            print(f"    {e}", file=sys.stderr)
    else:
        # No output file provided. Print to console
        run_as_users()
