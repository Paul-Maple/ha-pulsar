"""Represent Pulsar device."""

from __future__ import annotations

import struct
from typing import Any

from .connector import Connector
from .exceptions import (
    PulsarAddressError,
    PulsarCRCError,
    PulsarDataError,
    PulsarFrameError,
    PulsarProtocolError,
    PulsarRequestIdError,
)


class PulsarDevice:
    """Base class for Pulsar devices."""

    ADDR_SIZE = 4
    FUNC_SIZE = 1
    LEN_SIZE = 1
    ID_SIZE = 2
    CRC_SIZE = 2
    SERVICE_SIZE = ADDR_SIZE + FUNC_SIZE + LEN_SIZE + ID_SIZE + CRC_SIZE

    def __init__(
        self, connector: Connector, device_type: str, name: str, addr: int
    ) -> None:
        """Initialize Pulsar device.

        Args:
            connector: Serial connector instance.
            device_type: Device type identifier.
            name: Device name.
            addr: Device address.
        """
        self._connector = connector
        self._type = device_type
        self._name = name
        self._addr = addr
        self._request_id = 0

    def calculate_crc16(self, buf: bytearray | bytes, size: int, offset: int) -> int:
        """Calculate CRC-16-ModBus checksum.

        Args:
            buf: Buffer to calculate CRC for.
            size: Size of data to process.
            offset: Starting offset in buffer.

        Returns:
            CRC-16 value.

        """
        poly = 0xA001
        crc = 0xFFFF
        poly = 0xA001
        crc = 0xFFFF
        for i in range(size):
            crc ^= 0xFF & buf[i + offset]
            for _ in range(8):
                if crc & 0x0001:
                    crc = ((crc >> 1) & 0xFFFF) ^ poly
                else:
                    crc = (crc >> 1) & 0xFFFF
        return crc

    def write_bcd(
        self, val: int, buf: bytearray, size: int, offset: int, big_endian: bool
    ) -> bytearray:
        """Write integer as BCD to buffer.

        Args:
            val: Integer value to encode.
            buf: Target buffer.
            size: Number of bytes to write.
            offset: Starting offset in buffer.
            big_endian: True for big-endian, False for little-endian.

        Returns:
            Modified buffer.

        """
        for i in range(size):
            byte_val = int(val % 10)
            val = int(val / 10)
            byte_val |= int(val % 10) << 4
            val = int(val / 10)
            buf[size - i - 1 + offset if big_endian else i + offset] = byte_val
        return buf

    def write_hex(
        self, val: int, buf: bytearray, size: int, offset: int, big_endian: bool
    ) -> bytearray:
        """Write integer as hex to buffer.

        Args:
            val: Integer value to encode.
            buf: Target buffer.
            size: Number of bytes to write.
            offset: Starting offset in buffer.
            big_endian: True for big-endian, False for little-endian.

        Returns:
            Modified buffer.
        """
        for i in range(size):
            buf[size - i - 1 + offset if big_endian else i + offset] = val & 0xFF
            val >>= 8
        return buf

    def read_bcd(
        self, buf: bytearray | bytes, size: int, offset: int, big_endian: bool
    ) -> int:
        """Read BCD integer from buffer.

        Args:
            buf: Source buffer.
            size: Number of bytes to read.
            offset: Starting offset in buffer.
            big_endian: True for big-endian, False for little-endian.

        Returns:
            Decoded integer value.

        """
        res = 0
        for i in range(size):
            res *= 100
            bcd_byte = buf[i + offset if big_endian else size - i - 1 + offset]
            dec_byte = (bcd_byte & 0x0F) + 10 * ((bcd_byte >> 4) & 0x0F)
            res += dec_byte
        return res

    def read_int_from_hex(
        self, buf: bytearray | bytes, size: int, offset: int, big_endian: bool
    ) -> int:
        """Read integer from hex buffer.

        Args:
            buf: Source buffer.
            size: Number of bytes to read.
            offset: Starting offset in buffer.
            big_endian: True for big-endian, False for little-endian.

        Returns:
            Decoded integer value.

        """
        res = 0
        for i in range(size):
            res <<= 8
            res |= buf[i + offset if big_endian else size - i - 1 + offset]
        return res

    def read_float_from_hex(
        self, buf: bytearray | bytes, size: int, offset: int, big_endian: bool
    ) -> float | None:
        """Read float from hex buffer.

        Args:
            buf: Source buffer.
            size: Number of bytes to read.
            offset: Starting offset in buffer.
            big_endian: True for big-endian, False for little-endian.

        Returns:
            Decoded float value or None.

        Raises:
            PulsarDataError: If size is unsupported.

        """
        if big_endian:
            format_str = ">"
        else:
            format_str = "<"

        if size == 4:
            format_str += "f"
        elif size == 8:
            format_str += "d"
        elif size == 2:
            format_str += "e"
        else:
            raise PulsarDataError(f"Unsupported float size: {size}")

        val = struct.unpack(format_str, buf[offset : size + offset])

        if len(val) == 1:
            return val[0]
        if len(val) == 0:
            return None
        return val[0]  # Return first value if multiple

    def send_request(self, message: bytes, response_size: int) -> bytes:
        """Send request and receive response.

        Args:
            message: Request message.
            response_size: Expected response size.

        Returns:
            Response bytes.

        Raises:
            PulsarFrameError: If response validation fails.

        """
        addr = self.read_bcd(message, self.ADDR_SIZE, 0, True)
        request_id = self.read_int_from_hex(
            message, self.ID_SIZE, len(message) - self.ID_SIZE - self.CRC_SIZE, False
        )
        expected_response_size = response_size

        response = self._connector.send(message, response_size)

        self.check_response(response, expected_response_size, addr, request_id)

        return response

    def send_payload(
        self,
        payload: bytes,
        function: bytes,
        addr: int,
        request_id: int,
        expected_payload_size: int,
    ) -> bytes:
        """Send payload and receive response payload.

        Args:
            payload: Request payload.
            function: Function code.
            addr: Device address.
            request_id: Request ID.
            expected_payload_size: Expected payload size in response.

        Returns:
            Response payload bytes.

        Raises:
            PulsarProtocolError: If request preparation fails.
            PulsarFrameError: If response validation fails.

        """
        request = self.prepare_request(payload, function, addr, request_id)
        response = self.send_request(request, expected_payload_size + self.SERVICE_SIZE)
        start_ind = self.ADDR_SIZE + self.FUNC_SIZE + self.LEN_SIZE
        end_ind = 0 - self.ID_SIZE - self.CRC_SIZE
        return response[start_ind:end_ind]

    def check_response(
        self, response: bytes, expected_response_size: int, addr: int, request_id: int
    ) -> bool:
        """Validate response frame.

        Args:
            response: Response bytes from device.
            expected_response_size: Expected size of response.
            addr: Expected device address.
            request_id: Expected request ID.

        Returns:
            True if response is valid.

        Raises:
            PulsarFrameError: If frame is too short or wrong size.
            PulsarCRCError: If CRC check fails.
            PulsarAddressError: If address mismatch.
            PulsarRequestIdError: If request ID mismatch.

        """
        response_size = len(response)

        if response_size < self.SERVICE_SIZE:
            raise PulsarFrameError(
                f"Frame too short: {response_size} < {self.SERVICE_SIZE}"
            )

        if response_size != expected_response_size:
            raise PulsarFrameError(
                f"Unexpected frame size: {response_size} != {expected_response_size}"
            )

        if expected_response_size != response[5]:
            raise PulsarFrameError(
                f"Frame length mismatch: {expected_response_size} != {response[5]}"
            )

        # check crc16
        response_crc = self.read_int_from_hex(
            response, self.CRC_SIZE, response_size - self.CRC_SIZE, False
        )
        calc_response_crc = self.calculate_crc16(
            response, response_size - self.CRC_SIZE, 0
        )
        if response_crc != calc_response_crc:
            raise PulsarCRCError(
                f"CRC mismatch: {response_crc:04X} != {calc_response_crc:04X}"
            )

        # check address
        response_addr = self.read_bcd(response, self.ADDR_SIZE, 0, True)
        if response_addr != addr:
            raise PulsarAddressError(f"Address mismatch: {response_addr} != {addr}")

        # check request id
        response_request_id = self.read_int_from_hex(
            response, self.ID_SIZE, response_size - self.ID_SIZE - self.CRC_SIZE, False
        )
        if response_request_id != request_id:
            raise PulsarRequestIdError(
                f"Request ID mismatch: {response_request_id} != {request_id}"
            )

        return True

    def prepare_request(
        self, payload: bytes, function: bytes, addr: int, request_id: int
    ) -> bytes:
        """Prepare request frame.

        Args:
            payload: Request payload.
            function: Function code (1 byte).
            addr: Device address.
            request_id: Request ID.

        Returns:
            Complete request frame.

        Raises:
            PulsarProtocolError: If function code is invalid.

        """
        if len(function) != 1:
            raise PulsarProtocolError(
                f"Function code must be 1 byte, got {len(function)}"
            )

        payload_size = len(payload)
        request_size = payload_size + self.SERVICE_SIZE

        request = bytearray(request_size)

        self.write_bcd(addr, request, 4, 0, True)

        # function and size
        request[4] = function[0]
        request[5] = request_size

        # payload
        offset = self.ADDR_SIZE + self.FUNC_SIZE + self.LEN_SIZE
        request[offset : offset + payload_size] = payload

        # request ID
        self.write_hex(request_id, request, 2, request_size - 4, False)

        # CRC16
        crc = self.calculate_crc16(request, request_size - 2, 0)
        self.write_hex(crc, request, 2, request_size - 2, False)

        return bytes(request)

    @property
    def name(self) -> str:
        """Return device name.

        Returns:
            Device name.

        """
        return self._name

    @property
    def type(self) -> str:
        """Return device type.

        Returns:
            Device type identifier.

        """
        return self._type

    def next_request_id(self) -> int:
        """Get next request ID with wraparound."""
        self._request_id += 1
        if self._request_id > 65535:
            self._request_id = 0
        return self._request_id

    def getdata(self, _key: str) -> Any:
        """Get data value by key.

        Args:
            key: Data key identifier.

        Returns:
            Data value or None if not available.

        """
        return None
