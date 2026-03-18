import dearpygui.dearpygui as dpg
from src.audiodevicedefinition import AudioDeviceDefinition
from src.serialportaccess import SerialPortAccess


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

# Wrapper class around pySerial  (was meant to add better error messages and state, etc...
# But right now does almost nothing)
SerialPort = SerialPortAccess()


dpg.create_context()

def set_status_text(value: str):
    dpg.configure_item("StatusBar", default_value=value)

def com_port_changed(sender, data):
    global SerialPort
    set_status_text("Opening: " + data)
    try:
        SerialPort.open_port(data)
        set_status_text("Opened: " + data)
    except Exception as e:
        set_status_text(str(e))

def button_set_rts(sender, data):
    global SerialPort
    if SerialPort.is_valid():
        set_status_text("RTS Set")
        SerialPort.set_rts()
    else:
        set_status_text("Serial port not selected or invalid")

def button_clear_rts(sender, data):
    global SerialPort
    if SerialPort.is_valid():
        set_status_text("RTS Cleared")
        SerialPort.clear_rts()
    else:
        set_status_text("Serial port not selected or invalid")

def button_switch_local_audio(sender, data):
    global DefaultAudioDevice
    try:
        DefaultAudioDevice.set_as_default()
        set_status_text("Audio switched to default")
    except Exception as e:
        set_status_text("Unable to set audio: " + str(e))

def button_switch_radio_audio(sender, data):
    global RadioAudioDevice
    try:
        RadioAudioDevice.set_as_default()
        RadioAudioDevice.set_sink_volume()
        RadioAudioDevice.set_source_volume()
        set_status_text("Audio switched to radio")
    except Exception as e:
        set_status_text("Unable to set audio: " + str(e))


# Setup fonts, and make the default_font the default
with dpg.font_registry():
    # first argument ids the path to the .ttf or .otf file
    default_font = dpg.add_font("assets/NotoSans-Regular.ttf", 18)
    heading_font = dpg.add_font("assets/NotoSans-Bold.ttf", 18)

dpg.bind_font(default_font)


with dpg.window(tag="Primary Window"):

    dpg.add_text("Serial Port:", tag="HeadingSerialPort")
    dpg.bind_item_font(dpg.last_item(), heading_font)

    dpg.add_combo(SerialPortAccess.list_devices(), callback=com_port_changed)
    dpg.add_button(label="Set RTS", callback=button_set_rts)
    dpg.add_button(label="Clear RTS", callback=button_clear_rts)
    dpg.add_spacer()

    dpg.add_text("Audio Devices:", tag="HeadingAudio")
    dpg.bind_item_font(dpg.last_item(), heading_font)

    dpg.add_button(label="Local Audio", callback=button_switch_local_audio)
    dpg.add_button(label="Radio Audio", callback=button_switch_radio_audio)
    dpg.add_spacer()
    dpg.add_text("", tag="StatusBar")

# Add some rounded corners for fun, and turn off the window border as there is only a single window
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)

dpg.bind_theme(global_theme)

# Style the Text a little too I guess
with dpg.theme() as heading_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_Text, (160, 70, 40))

dpg.bind_item_theme("HeadingSerialPort", heading_theme)
dpg.bind_item_theme("HeadingAudio", heading_theme)


# Single window
dpg.create_viewport(title='FTM-150 Helper', width=500, height=300)
dpg.set_viewport_resizable(True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.start_dearpygui()
dpg.destroy_context()