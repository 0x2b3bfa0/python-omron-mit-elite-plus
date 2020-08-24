# Omron MIT Elite Plus HEM-7301-ITKE7
Python script to extract measurements from an Omron MIT Elite Plus (HEM-7301-ITKE7) blood pressure monitor with USB support (0590:0028).

***

Based on [https://usb2me.wordpress.com/2013/02/06/omron-mit-elite-plus-hem-7301-itke7](https://web.archive.org/web/20200704141615/https://usb2me.wordpress.com/2013/02/06/omron-mit-elite-plus-hem-7301-itke7/)

> _This upper arm blood pressure monitor has memory for last 90 measurements. It records date, time, systolic/diastolic pressure and pulse. It has somewhat more complicated USB protocol using request/response packets. It has also support for wakeup request._

## Installing

```bash
git clone https://github.com/0x2b3bfa0/python-omron-mit-elite-plus.git
cd python-omron-mit-elite-plus
pip install -r requirements.txt
python omron_mit_elite_plus.py
```
