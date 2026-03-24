import dearpygui.dearpygui as dpg
from src.serialportaccess import SerialPortAccess
from src.configuration import Configuration


# Wrapper class around pySerial  (was meant to add better error messages and state, etc...
# But right now does almost nothing)
SerialPort = SerialPortAccess()
AppConf = Configuration("conf.toml")


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

def button_refresh_ports(sender, data):
    devices = SerialPortAccess.list_devices()
    dpg.configure_item("PortListCombo", items=devices)
    set_status_text("Found {} devices".format(len(devices)))

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
    global AppConf
    try:
        if AppConf.get_default_audio_device().switch():
            set_status_text("Audio switched to Local")
        else:
            set_status_text("Unable to switch audio to local")
    except Exception as e:
        set_status_text("Unable to set audio: " + str(e))

def button_switch_radio_audio(sender, data):
    global AppConf
    try:
        if AppConf.get_radio_audio_device().switch():
            set_status_text("Audio switched to Radio")
        else:
            set_status_text("Unable to switch audio to radio")
    except Exception as e:
        set_status_text("Unable to set audio: " + str(e))


# Start the UI
dpg.create_context()

# Setup fonts.   Make default_font the default
with dpg.font_registry():
    # first argument ids the path to the .ttf or .otf file
    default_font = dpg.add_font("assets/NotoSans-Regular.ttf", 18)
    heading_font = dpg.add_font("assets/NotoSans-Bold.ttf", 18)

dpg.bind_font(default_font)

# Setup global theme.  Rounded corners for fun, and turn off the window border as there is only a single window
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)

dpg.bind_theme(global_theme)

# Add second theme.  Used to change the color of text
with dpg.theme() as text_heading_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_Text, (160, 70, 40))

# Finally, setup hotkeys
with dpg.handler_registry():
    dpg.add_key_press_handler(dpg.mvKey_S, callback=button_set_rts)
    dpg.add_key_press_handler(dpg.mvKey_C, callback=button_clear_rts)
    dpg.add_key_press_handler(dpg.mvKey_L, callback=button_switch_local_audio)
    dpg.add_key_press_handler(dpg.mvKey_R, callback=button_switch_radio_audio)
    dpg.add_key_press_handler(dpg.mvKey_Q, callback=lambda: dpg.stop_dearpygui())


with dpg.window(tag="Primary Window"):
    dpg.add_text("Serial Port:")
    dpg.bind_item_font(dpg.last_item(), heading_font)
    dpg.bind_item_theme(dpg.last_item(), text_heading_theme)

    with dpg.group(horizontal=True):
        dpg.add_spacer(width=4)
        dpg.add_combo(SerialPortAccess.list_devices(), callback=com_port_changed, tag="PortListCombo")
        dpg.add_button(label="Refresh", callback=button_refresh_ports)

    dpg.add_spacer(height=8)

    dpg.add_text("Toggle PTT:")
    dpg.bind_item_font(dpg.last_item(), heading_font)
    dpg.bind_item_theme(dpg.last_item(), text_heading_theme)

    with dpg.group(horizontal=True):
        dpg.add_spacer(width=4)
        dpg.add_button(label="Set RTS", callback=button_set_rts)
        dpg.add_button(label="Clear RTS", callback=button_clear_rts)

    dpg.add_spacer(height=8)

    dpg.add_text("Audio Devices:")
    dpg.bind_item_font(dpg.last_item(), heading_font)
    dpg.bind_item_theme(dpg.last_item(), text_heading_theme)

    with dpg.group(horizontal=True):
        dpg.add_spacer(width=4)
        dpg.add_button(label="Local Audio", callback=button_switch_local_audio)
        dpg.add_button(label="Radio Audio", callback=button_switch_radio_audio)

    dpg.add_spacer(height=8)

    dpg.add_text("", tag="StatusBar")


# Single window
dpg.create_viewport(title='Radio Interface Helper', width=500, height=300)
dpg.set_viewport_resizable(True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.start_dearpygui()
dpg.destroy_context()