import serial, serial.tools.list_ports

class SerialPortAccess:
    def __init__(self):
        self._serial: serial.SerialBase | None = None

    @staticmethod
    def list_devices():
        comports = [str(port.device) for port in serial.tools.list_ports.comports()]
        return list(reversed(comports))

    def open_port(self, port: str):
        self.close_port()
        self._serial = serial.Serial(port=port, baudrate=9600, timeout=0)
        self.clear_rts() # RTS is set upon opening on my system

    def close_port(self):
        try:
            if self.is_valid():
                self._serial.close()
        except serial.SerialException as e:
            pass

    def is_valid(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def get_rts(self) -> bool:
        return self._serial.rts

    def set_rts(self):
        self._serial.rts = True  # this property is a @setter

    def clear_rts(self):
        self._serial.rts = False
