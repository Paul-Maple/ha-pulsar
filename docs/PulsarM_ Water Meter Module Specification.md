# **PulsarM: Water Meter Module Specification**

Module Type: Water Meter (Pulse Counter / Integrated)  
Protocol: PulsarM (Extension)

## **1\. Archives Support**

The device supports the following archive types (Function 0x06):

* **Hourly:** Depth \~62 days (1488 records).  
* **Daily:** Depth \~6 months (184 records).  
* **Monthly:** Depth \~5 years (60 records).

## **2\. Channels Table (Read via 0x01, Write via 0x02)**

| Channel | Name | Access | Format | Description |
| :---- | :---- | :---- | :---- | :---- |
| **1** | **Volume** | R/W | DOUBLE / FLOAT64 | Accumulated volume ($m^3$). *Note: See parameter 0x0004 (Pulse Weight) if applicable.* |

## **3\. Parameters Table (Read via 0x0A, Write via 0x0B)**

| Index (Hex) | Parameter Name | Access | Format | Description |
| :---- | :---- | :---- | :---- | :---- |
| **0x0000** | **Device ID** | R | UINT16 | Unique Device Identifier. |
| **0x0001** | **Network Address** | R/W | UINT32 | Logical address on the bus \[1...99999999\]. |
| **0x0002** | **Firmware Version** | R | UINT64 | Encoding: Byte 0-1: FW Number Byte 2-3: HW Version Byte 4-5: SW Version Byte 6: Revision Byte 7: Modification |
| **0x0004** | **Pulse Weight** | R/W | FLOAT32 | Volume per disk turn/pulse (e.g., 0.01 $m^3$). |
| **0x0005** | **Write Protection** | R | UINT16 | 0x0000: Write Allowed 0x0001: Write Forbidden |
| **0x0006** | **MCU Cycles** | R/W | UINT32 | Internal counter (Diagnostic). |
| **0x0007** | **Current Errors** | R | UINT32 | Bitmask of current errors (see Section 4). |
| **0x0010** | **Accumulated Errors** | R/W | UINT32 | History of errors (Sticky bits). |
| **0x0040** | **Environment Temp** | R | INT8 | Temperature in Celsius (approximate). |
| **0x0041** | **Battery Voltage** | R | UINT16 | Voltage in mV (e.g., 3600 \= 3.6V). |

## **4\. Error Flags (Parameter 0x0007)**

The "Current Errors" parameter is a bitmask.

| Bit | Name | Description |
| :---- | :---- | :---- |
| **0** | **Reset** | Power-on reset occurred. |
| **1** | **Low Battery** | Battery voltage is below threshold. |
| **2** | **EEPROM Error** | Memory read/write failure. |
| **3** | **Flow Error** | Backflow detected (Negative flow). |
| **4** | **Reed Switch** | Reed switch error / bounce / stuck. |
| **5** | **Transceiver** | Radio module failure. |
| **6** | **Quartz** | RTC (Real Time Clock) crystal failure. |
| **7** | **Magnetic Tamper** | Strong magnetic field detected (Magnet applied). |
| **8** | **Module Removal** | Module removed from the mechanical flow part. |
| **9-15** | *Reserved* |  |

## **5\. Additional Info**

* **Float Format:** Adheres to IEEE 754\.  
* **Byte Order:** Little Endian (LSB First).  
* **Access:** R \= Read Only, R/W \= Read/Write.