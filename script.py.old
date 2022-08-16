import mido
import PySimpleGUI as sg
from pythonosc import udp_client

from copy import deepcopy
from pathlib import Path
import time
import json

from objects import Binding, Action
from keycodes import Keycodes

midi_devices = []
midi_devices_open = []
midi_bindings = []
last_midi_input = None

# -----------------------------------------------------------
# Config stuff
config = {
    'osc_ip': '127.0.0.1',
    'osc_port': '12345',
    'bindings': []
}


def config_load():
    with open('config.json', 'r') as config_file:
        config_file_content = json.load(config_file)
        for key in config:
            if key in config_file_content:
                config.update({key: config_file_content.get(key)})
        config_load_bindings()


def save_config():
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=2)


def config_load_bindings():
    for d in config['bindings']:
        b = Binding.fromDict(d)
        midi_bindings.append(b)


def config_append_binding(binding):
    config['bindings'].append({
        'device': binding.device_name,
        'voice': binding.voice,
        'channel': str(binding.channel),
        'address': str(binding.address),
        'actions': list(map(Action.toDict, binding.actions))
    })
    save_config()


def config_update_binding(binding):
    for cb in config['bindings']:
        if cb['device'] == binding.device_name and cb['voice'] == binding.voice and int(cb['channel']) == binding.channel and int(cb['address']) == binding.address:
            cb['actions'] = list(map(Action.toDict, binding.actions))
    save_config()


def csv_export():
    filename = 'export' + time.strftime("%Y%m%d-%H%M%S") + '.csv'
    with open(filename, 'w+') as csv:
        csv.write('device,voice,channel,address,actions\n')
        for cb in config['bindings']:
            csv.write(cb['device'] + ';' + cb['voice'] + ';' +
                      cb['channel'] + ';' + cb['address'])
            for action in cb['actions']:
                csv.write(';' +
                          action['message'] + ';' +
                          str(action['values']['low']) + ';' +
                          str(action['values']['high']) + '\n')


config_load()

# -----------------------------------------------------------
# GUI Stuff


sg.theme('DarkBrown')

# Main window

binding_table_headings = ['Device', 'Type',
                          'Channel', 'Note/Ctrl', 'OSC']
binding_table_cols_width = [16, 12, 8, 8, 16]


def make_mainwindow():
    column1 = [[sg.Text('Midi Devices')],
               [sg.Listbox(values=midi_devices,
                           size=(30, 10),
                           key='_devicelist_',
                           enable_events=True
                           )],
               [sg.Button('Refresh')],
               [sg.HorizontalSeparator()],
               [sg.Text('OSC out address and port')],
               [sg.Input(config.get('osc_ip'), key='_oscoutip_', size=(15, 1), enable_events=True),
               sg.Input(config.get('osc_port'), key='_oscoutport_', size=(10, 1), enable_events=True)],
               [sg.Button('Save settings')],
               [sg.Text('Restart program to apply settings')],

               ]

    column2 = [[sg.Table(values=list(map(Binding.toArray, midi_bindings)),
                         headings=binding_table_headings,
                         col_widths=binding_table_cols_width,
                         auto_size_columns=False,
                         justification='left',
                         num_rows=20,
                         key='_bindingtable_',
                         enable_events=True,
                         enable_click_events=True,
                         select_mode=sg.TABLE_SELECT_MODE_BROWSE
                         )],
               [sg.Button('New Binding'),
               sg.Button('Delete Selected'),
               sg.Button('Export CSV')],
               [sg.Text('Feedback')],
               [sg.Multiline('',
                             size=(72, 5),
                             key='_statusbar_',
                             autoscroll=True
                             )]
               ]
    layout = [[sg.Column(column1), sg.Column(column2)]]
    return sg.Window('MidiToOsc', layout, finalize=True)


def make_bindingwindow():
    frameinput = [[sg.Frame(layout=[[sg.Text('Press a midi key')],
                                    [sg.StatusBar('waiting for input...',
                                                  key='_devicename_',
                                                  size=(43, 1)
                                                  )],
                                    [sg.StatusBar('waiting for input...',
                                                  key='_midimessage_',
                                                  size=(43, 1)
                                                  )
                                     ]], title='Input')
                   ]]

    frameosc = [[sg.Frame(layout=[[sg.Input('/example',
                                            key='_bindoscmessage_',
                                            size=(50, 1)
                                            )],
                                  [sg.Text('Output value range')],
                                  [sg.Input('0.0', key='_bindosclow_', size=(10, 1)),
                                  sg.Input('1.0', key='_bindoschigh_', size=(10, 1))]
                                  ], title='OSC Message')
                 ]]

    layout = [frameinput,
              frameosc,
              [sg.Button('Save Binding'),
               sg.Button('Cancel Binding')]
              ]
    return sg.Window('New MIDI Binding', layout, margins=(25, 25), finalize=True)


mainwindow, bindwindow = make_mainwindow(), None

mainwindow['_devicelist_'].bind('<Double-Button-1>', "+-double click-")
mainwindow['_devicelist_'].widget.configure(activestyle='none')


def log(text):
    mainwindow['_statusbar_'].update(str(text) + '\n', append=True)


# -----------------------------------------------------------
# OSC Stuff

osc_client = udp_client.SimpleUDPClient(
    config.get('osc_ip'),
    int(config.get('osc_port'))
)


def osc_send(address, value):
    log(address + " " + str(value))
    osc_client.send_message(address, value)

# borrowed from Arduino


def map_float(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# -----------------------------------------------------------
# MIDI Stuff


def midi_init():
    global midi_devices
    midi_devices = []
    for device in mido.get_input_names():
        midi_devices.append(device)
    mainwindow['_devicelist_'].update(values=midi_devices)


def midi_connect(name):
    global midi_devices_open
    try:
        # TODO: check if already connected to this device
        midi_devices_open.append(mido.open_input(name))
        log('connected to ' + name)
    except:
        log('could not connect to ' + name)


def midi_read_inputs():
    if len(midi_devices_open) > 0:
        for device in midi_devices_open:
            # TODO: Check if device still exists. device.closed does not do this
            for msg in device.iter_pending():
                if msg.type not in ['control_change', 'note_on']:
                    continue
                bind = Binding(
                    device_name=device.name,
                    voice=msg.type,
                    channel=msg.channel,
                    address=msg.control if msg.type == 'control_change' else msg.note,
                    value=msg.value if msg.type == 'control_change' else round(
                        msg.velocity, 0),
                )
                midi_handle_message(bind)


def midi_handle_message(bind):
    global last_midi_input
    if bindwindow != None:
        last_midi_input = bind
        bindwindow['_devicename_'].update(bind.device_name)
        bindwindow['_midimessage_'].update(
            bind.voice +
            " channel " + str(bind.channel) +
            " note/control " + str(bind.address)
        )
    else:
        midi_execute_if_exists(bind)


def midi_save_binding(close_on_save):
    global last_midi_input, midi_bindings
    if last_midi_input == None:
        return

    bind = None
    exists = False

    for b in midi_bindings:
        if b.equals(last_midi_input):
            exists = True
            bind = b

    if not exists:
        bind = deepcopy(last_midi_input)

    oscMsg = bindwindow['_bindoscmessage_'].get().strip()
    if oscMsg != '':
        oscAction = Action(
            action_message=oscMsg,
            osc_values={
                'low': float(bindwindow['_bindosclow_'].get().strip()),
                'high': float(bindwindow['_bindoschigh_'].get().strip())
            }
        )
        bind.actions.append(oscAction)
        if not exists:
            midi_bindings.append(bind)
            config_append_binding(bind)
        else:
            config_update_binding(bind)

    bindwindow.write_event_value('Exit', None)
    mainwindow['_bindingtable_'].update(
        values=map(Binding.toArray, midi_bindings))


def midi_execute_if_exists(incoming_bind):
    global midi_bindings
    for bind in midi_bindings:
        if bind.equals(incoming_bind):
            for action in bind.actions:
                mapped_value = map_float(incoming_bind.value,
                                         0,
                                         127,
                                         action.osc_values['low'],
                                         action.osc_values['high']
                                         )
                osc_send(action.action_message, mapped_value)


midi_init()


# -----------------------------------------------------------
# Main loop


while True:
    # Handle GUI events -------------------------------------
    midi_read_inputs()

    window, event, values = sg.read_all_windows(timeout=20)
    if event == '_devicelist_+-double click-':
        midi_connect(midi_devices[mainwindow['_devicelist_'].GetIndexes()[0]])
    elif event == 'Refresh':
        midi_init()
    elif event == '_oscoutip_':
        config.update({'osc_ip': values['_oscoutip_']})
    elif event == '_oscoutport_':
        config.update({'osc_port': values['_oscoutport_']})
    elif event == 'Save settings':
        save_config()
    elif event == 'New Binding':
        if bindwindow == None:
            bindwindow = make_bindingwindow()
        else:
            bindwindow.force_focus()
    elif event == 'Export CSV':
        csv_export()
    elif event == 'Save Binding':
        midi_save_binding(True)
    elif event == sg.WIN_CLOSED or event == 'Exit':
        window.close()
        if window == bindwindow:
            bindwindow = None
        elif window == mainwindow:
            break
    elif event in ('Quit', None):
        break

# -----------------------------------------------------------
# End of main loop

mainwindow.close()
