#!/usr/bin/env python3
"""
RTS Control GUI (Linux) using Tkinter + PySerial

Features:
- Dropdown to select available serial ports
- Refresh button to re-enumerate ports
- Controls to Toggle RTS / set RTS On / set RTS Off
- Toggle button background reflects the current RTS state

Dependencies:
  pip install pyserial
"""

import sys
import subprocess
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk, messagebox
from pipewiredump import PipeWireDump
import serial
from serial.tools import list_ports


@dataclass
class AudioDeviceDefinition:
    """
    This is a helper class to abstract talking to the OS about the audio devices
    We are working with both a Sink (speaker) and Source (microphone) device as a pair
    Is uses the PipeWireDump (pw-dump) to turns PipeWire node names into ids at runtime
    And wp-ctl to set volumes and default devices
    """
    sink: str
    source: str
    sink_volume: float
    source_volume: float
    sink_id: int = None
    source_id: int = None

    @staticmethod
    def _get_pw_dump(force_refresh=False) -> PipeWireDump:
        """
        There's logic that says it should always refresh.  Who knows what the user is plugging in and removing while
        running this program?
        """
        if not hasattr(AudioDeviceDefinition, '._pwd') or force_refresh:
            AudioDeviceDefinition._pwd = PipeWireDump()
            AudioDeviceDefinition._pwd.refresh()
        return AudioDeviceDefinition._pwd

    def get_sink_id(self) -> int:
        return self._get_pw_dump().get_node_id_by_name(self.sink)

    def get_source_id(self) -> int:
        return self._get_pw_dump().get_node_id_by_name(self.source)

    @staticmethod
    def _set_volume(node_id: int, volume: float) -> None:
        subprocess.run(["wpctl", "set-volume", str(node_id), str(volume)])

    def set_sink_volume(self) -> None:
        self._set_volume(self.get_sink_id(), self.sink_volume)

    def set_source_volume(self) -> None:
        self._set_volume(self.get_source_id(), self.source_volume)
        pass

    @staticmethod
    def _set_default(node_id: int) -> None:
        subprocess.run(["wpctl", "set-default", str(node_id)])

    def set_as_default(self):
        self._set_default(self.get_sink_id())
        self._set_default(self.get_source_id())


DefaultAudioDevice = AudioDeviceDefinition(
    sink          = 'alsa_output.usb-miniDSP_miniDSP_2x4HD-00.analog-stereo',
    source        = 'alsa_input.usb-ARTURIA_MiniFuse_2_8840400501033904-00.HiFi__Line3__source',
    sink_volume   = 0.5,
    source_volume = 1.0
)

RadioAudioDevice = AudioDeviceDefinition(
    sink          = 'alsa_output.usb-C-Media_Electronics_Inc._USB_Audio_Device-00.analog-stereo',
    source        = 'alsa_input.usb-C-Media_Electronics_Inc._USB_Audio_Device-00.mono-fallback',
    sink_volume   = 0.7,
    source_volume = 0.38
)


class RTSControllerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RTS Control (Linux)")
        self.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam') # Popular themes: 'clam', 'alt', 'default', 'classic'

        # Serial state
        self.ser = None
        self.selected_port = tk.StringVar()

        # Build UI
        self._build_ui()

        # Populate ports on startup
        self.refresh_ports()

        # When closing the window, ensure we close the serial port
        self.protocol("WM_DELETE_WINDOW", self.on_close)


    def _build_ui(self):
        pad = {"padx": 10, "pady": 10}

        # Row 0: Port selection + Refresh
        top_frame = ttk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="ew", **pad)

        ttk.Label(top_frame, text="Serial Port:").grid(row=0, column=0, sticky="w")

        self.port_combo = ttk.Combobox(
            top_frame, textvariable=self.selected_port, state="readonly", width=35
        )
        self.port_combo.grid(row=0, column=1, sticky="w", padx=(5, 5))
        self.port_combo.bind("<<ComboboxSelected>>", self.on_port_selected)

        self.refresh_btn = ttk.Button(
            top_frame, text="Refresh", command=self.refresh_ports
        )
        self.refresh_btn.grid(row=0, column=2, sticky="w")

        # Row 1: Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=0, sticky="ew", **pad)

        # Use tk.Button for the toggle so we can reliably set background colors
        self.toggle_btn = tk.Button(
            btn_frame, text="Toggle RTS", width=12, command=self.toggle_rts
        )
        self.toggle_btn.grid(row=0, column=0, padx=(0, 8))
        self.toggle_btn.config(state="disabled")
        self._update_toggle_btn_color(None)  # Set initial color to disabled/gray

        self.on_btn = ttk.Button(
            btn_frame, text="RTS On", command=lambda: self.set_rts(True)
        )
        self.on_btn.grid(row=0, column=1, padx=(0, 8))
        self.on_btn.state(["disabled"])

        self.off_btn = ttk.Button(
            btn_frame, text="RTS Off", command=lambda: self.set_rts(False)
        )
        self.off_btn.grid(row=0, column=2)
        self.off_btn.state(["disabled"])

        # Row 2: Audio buttons
        audio_frame = ttk.Frame(self)
        audio_frame.grid(row=2, column=0, sticky="ew", **pad)

        self.default_audio_btn = ttk.Button(
            audio_frame, text="Default Audio", command=self.set_default_audio
        )
        self.default_audio_btn.grid(row=0, column=0, padx=(0, 8))

        self.radio_audio_btn = ttk.Button(
            audio_frame, text="Radio Audio", command=self.set_radio_audio
        )
        self.radio_audio_btn.grid(row=0, column=1)

        # Status bar
        self.status_var = tk.StringVar(value="Select a port to begin.")
        status = ttk.Label(
            self, textvariable=self.status_var, relief="sunken", anchor="w"
        )
        status.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

    def refresh_ports(self):
        """Re-enumerate available serial ports and update the combobox."""
        ports = reversed(list_ports.comports())
        device_list = [p.device for p in ports]
        current = self.selected_port.get()

        self.port_combo["values"] = device_list

        if current in device_list:
            # Keep the current selection if it still exists
            self.port_combo.set(current)
        elif device_list:
            # Select the first available port if no current selection or current not in list
            self.port_combo.set(device_list[0])
            # Enable controls without opening the port (only on startup when no port was selected)
            self.on_port_selected()
            self.set_rts(False)
        else:
            # Clear selection if no ports available
            self.port_combo.set("")
            self.close_port()

        self.status_var.set(f"Found {len(device_list)} port(s).")

    def on_port_selected(self, event=None):
        """Enable controls when a port is selected, but don't automatically open it."""
        selected = self.selected_port.get().strip()
        if not selected:
            self.close_port()
            return
        
        # If a different port is selected, close the current port
        if self.ser is not None and self.ser.is_open:
            current_open_port = self.ser.port
            if current_open_port != selected:
                self.close_port(silent=True)
        
        # Enable controls when a port is selected
        self._set_controls_enabled(True)
        if self.ser is not None and self.ser.is_open:
            self._update_toggle_btn_color(self.ser.rts)
        else:
            self._update_toggle_btn_color(None)  # Gray since port not open yet
        self.status_var.set(f"Port selected: {selected}. Click a button to open and control RTS.")

    def open_port(self, port_name: str):
        """Open the requested serial port and enable controls."""
        # Close any currently open port
        self.close_port(silent=True)

        try:
            # Open with default settings; these are irrelevant for RTS control
            self.ser = serial.Serial(port=port_name, baudrate=9600, timeout=0)
            self.status_var.set(f"Opened {port_name}")
            self._set_controls_enabled(True)
            # Update the toggle button's color to reflect current RTS state
            self._update_toggle_btn_color(self.ser.rts)
        except serial.SerialException as e:
            self.ser = None
            self._set_controls_enabled(False)
            self._update_toggle_btn_color(None)
            messagebox.showerror("Port Error", f"Failed to open {port_name}\n\n{e}")
            self.status_var.set("Failed to open port. See error.")

    def close_port(self, silent=False):
        """Close the current serial port if open and disable controls."""
        if self.ser is not None:
            try:
                if self.ser.is_open:
                    self.ser.close()
            except Exception:
                pass
            finally:
                self.ser = None

        self._set_controls_enabled(False)
        self._update_toggle_btn_color(None)

        if not silent:
            self.status_var.set("Port closed.")

    def _set_controls_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.toggle_btn.config(state=state)
        if enabled:
            self.on_btn.state(["!disabled"])
            self.off_btn.state(["!disabled"])
        else:
            self.on_btn.state(["disabled"])
            self.off_btn.state(["disabled"])

    def _update_toggle_btn_color(self, rts_state):
        """
        Update the toggle button color based on RTS state.
        rts_state: True (ON), False (OFF), or None (unknown/disabled)
        """
        if rts_state is True:
            self.toggle_btn.config(
                bg="lime green",
                activebackground="lime green",
                fg="black",
                text="Toggle RTS (ON)",
            )
        elif rts_state is False:
            self.toggle_btn.config(
                bg="tomato",
                activebackground="tomato",
                fg="black",
                text="Toggle RTS (OFF)",
            )
        else:
            # Unknown/disabled
            self.toggle_btn.config(
                bg="light gray",
                activebackground="light gray",
                fg="black",
                text="Toggle RTS",
            )

    def toggle_rts(self):
        """Toggle RTS state on the open port."""
        if not self._port_ready():
            return

        try:
            new_state = not self.ser.rts
            self.ser.rts = new_state
            self._update_toggle_btn_color(self.ser.rts)
            self.status_var.set(f"RTS {'ON' if new_state else 'OFF'}")
        except serial.SerialException as e:
            messagebox.showerror("RTS Error", f"Failed to toggle RTS\n\n{e}")
            self.status_var.set("Error toggling RTS.")

    def set_rts(self, state: bool):
        """Set RTS to the given state on the open port."""
        if not self._port_ready():
            return

        try:
            self.ser.rts = state
            self._update_toggle_btn_color(self.ser.rts)
            self.status_var.set(f"RTS {'ON' if state else 'OFF'}")
        except serial.SerialException as e:
            messagebox.showerror(
                "RTS Error", f"Failed to set RTS {'ON' if state else 'OFF'}\n\n{e}"
            )
            self.status_var.set("Error setting RTS.")

    def _port_ready(self) -> bool:
        """Validate that a serial port is open and ready. If not but a port is selected, try to open it."""
        if self.ser is None or not self.ser.is_open:
            # Try to open the selected port
            selected = self.selected_port.get().strip()
            if selected:
                self.open_port(selected)
                if self.ser is not None and self.ser.is_open:
                    return True
            
            messagebox.showwarning(
                "No Port", "Please select a serial port first."
            )
            return False
        return True

    def set_default_audio(self):
        global DefaultAudioDevice
        DefaultAudioDevice.set_as_default()
        self.status_var.set("Switched to Default Audio")

    def set_radio_audio(self):
        global RadioAudioDevice
        RadioAudioDevice.set_as_default()
        RadioAudioDevice.set_sink_volume()
        RadioAudioDevice.set_source_volume()
        self.status_var.set("Switched to Radio Audio")

    def on_close(self):
        """Cleanup and exit."""
        self.close_port(silent=True)
        self.destroy()


def main():
    app = RTSControllerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
