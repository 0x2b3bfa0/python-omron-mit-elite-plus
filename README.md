# Omron MIT Elite Plus HEM-7301-ITKE7
Python script to extract measurements from an Omron MIT Elite Plus (`HEM-7301-ITKE7`) blood pressure monitor with USB support (`0590:0028`). This has also been tested to work with an Omron T9P (`HEM-759P-C1`) using the `HHX-CABLE-USB1`. This cable claims to work with `HJ-720IT`, `HEM-7080IT-E` and `HEM-790IT` models, although this has not been tested yet.

***

Based on [https://usb2me.wordpress.com/2013/02/06/omron-mit-elite-plus-hem-7301-itke7](https://web.archive.org/web/20200704141615/https://usb2me.wordpress.com/2013/02/06/omron-mit-elite-plus-hem-7301-itke7/) ([direct link](https://usb2me.wordpress.com/2013/02/06/omron-mit-elite-plus-hem-7301-itke7)).

> _This upper arm blood pressure monitor has memory for last 90 measurements. It records date, time, systolic/diastolic pressure and pulse. It has somewhat more complicated USB protocol using request/response packets. It has also support for wakeup request._

## Installing

```bash
git clone https://github.com/0x2b3bfa0/python-omron-mit-elite-plus.git
cd python-omron-mit-elite-plus
pip install -r requirements.txt
```

## Linux permissions
By default, this script will need to be run as root to gain privileges to access the device. The `elevate` python module is used to request this automatically if running as the current user fails due to permissions issues. In the long term, it is recommended that udev rules be added to allow any (or selected) users to access the USB device so that running as root is not required. To do this:
1. Copy the [`73-omron-bpm.rules`](./73-omron-bpm.rules) file to `/etc/udev/rules.d/73-omron-bpm.rules`.
2. Run `sudo udevadm control --reload-rules && sudo udevadm trigger` as per [this post](https://unix.stackexchange.com/a/39371) to apply the new rules.

## Usage
This script is controlled through command line arguments. For example, to read all data on the monitor, write this to `output.csv` and then clear it, run
```
python omron_elite_plus.py -r -c -o output.csv
```

### Options
```
usage: omron_elite_plus.py [-h] [-r] [--correct-times]
                        [-c] [-t] [-n] [-o OUTPUT]

Tool for connecting to Omron branded blood pressure
monitors

options:
-h, --help            show this help message and exit
-r, --read            Read all data stored on the
                        monitor.
--correct-times       When reading, adds an offset from
                        the computer's time to the
                        monitor's time for each record to
                        correct for the date and time on
                        the monitor not being set
                        correctly.
-c, --clear           Request that the monitor clear
                        its internal memory after
                        reading.
-t, --time            Get the current time from the
                        monitor.
-n, --number          Get the number of records stored
                        on the monitor.
-o OUTPUT, --output OUTPUT
                        Write the results to the provided
                        file instead of to the console.
```

## Alternatives

* [UBPM - Universal Blood Pressure Manager](https://codeberg.org/LazyT/ubpm), a [Qt](https://qt.io) graphical application for managing your blood pressure meter, compatible with macOS, Linux and Windows.
