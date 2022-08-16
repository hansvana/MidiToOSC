from enum import auto
import mido
import PySimpleGUI as sg
from pythonosc import udp_client

from copy import deepcopy
import json

from objects import Binding

midi_devices_detected = []
midi_devices_connected = []
midi_bindings = []
last_midi_input = None
last_clicked_cell = (-1, -1)

# -----------------------------------------------------------
# Config stuff
config = {
    'osc_ip': '127.0.0.1',
    'osc_port': '12345',
    'midi_auto_connect': False,
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
        'actions': binding.actions
    })
    save_config()


def config_update_binding(binding):
    for cb in config['bindings']:
        if cb['device'] == binding.device_name and cb['voice'] == binding.voice and int(cb['channel']) == binding.channel and int(cb['address']) == binding.address:
            cb['actions'] = binding.actions
    save_config()


config_load()

# -----------------------------------------------------------
# GUI Stuff


sg.theme('DarkBrown')

# Main window

binding_table_headings = ['Device', 'Type',
                          'Channel', 'Note/Ctrl', 'Actions']
binding_table_cols_width = [16, 12, 8, 8, 16]


def make_mainwindow():
    column1 = [[sg.Text('Midi Devices')],
               [sg.Listbox(values=midi_devices_detected,
                           size=(30, 10),
                           key='_devicelist_',
                           enable_events=True
                           )],
               [sg.Button('Refresh')],
               [sg.T("")],
               [sg.HorizontalSeparator()],
               [sg.Text('Settings')],
               [sg.Checkbox('Auto connect to midi devices', key='_autoconnectmidi_', enable_events=True,
                            default=config.get('midi_auto_connect'))],
               [sg.Text('OSC out address and port')],
               [sg.Input(config.get('osc_ip'), key='_oscoutip_', size=(15, 1), enable_events=True),
               sg.Input(config.get('osc_port'), key='_oscoutport_', size=(10, 1), enable_events=True)],
               [sg.T("")],
               [sg.Button('Save settings')],
               [sg.Text('Restart program to apply settings')]
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
               [sg.Button('New Binding')],
               [sg.Multiline('',
                             size=(72, 5),
                             key='_statusbar_',
                             autoscroll=True
                             )]
               ]
    layout = [
        [sg.Column(column1), sg.Column(column2)],
        [sg.Push(), sg.Text('v0.0.3')]
    ]

    return sg.Window('MidiToOsc', layout, margins=(25, 25), finalize=True)

# Dialog windows


def make_midiwindow():
    layout = [[sg.Text('Waiting for input from your midi device...')]
              ]

    return sg.Window('New MIDI Binding', layout, margins=(25, 25), finalize=True)


def make_actionwindow(row=0, actionstring=''):
    layout = [[sg.Text('Type your actions here, separated by comma.')],
              [sg.Input(row, key='_actionrow_', visible=False)],
              [sg.Input(actionstring, key='_actionstring_')],
              [sg.Button('Save', key='_UpdateAction_',
                         bind_return_key=True)]
              ]

    return sg.Window('Update action', layout, margins=(25, 25), finalize=True)


mainwindow = make_mainwindow()
midiwindow, actionwindow = None, None

mainwindow['_bindingtable_'].bind('<Double-Button-1>', "+-double click-")
mainwindow['_devicelist_'].bind('<Double-Button-1>', "+-double click-")
mainwindow['_devicelist_'].widget.configure(activestyle='none')


def log(text):
    mainwindow['_statusbar_'].update(str(text) + '\n', append=True)

# -----------------------------------------------------------
# MIDI Stuff


def midi_init():
    global midi_devices_detected
    midi_devices_detected = []
    auto_connect = config.get('midi_auto_connect')
    for device in mido.get_input_names():
        midi_devices_detected.append(device)
        if auto_connect:
            midi_connect(device)

    mainwindow['_devicelist_'].update(values=midi_devices_detected)


def midi_connect(name):
    global midi_devices_connected
    try:
        # TODO: check if already connected to this device
        midi_devices_connected.append(mido.open_input(name))
        log('Connected to ' + name)
    except:
        log('Could not connect to ' + name + '. Already connected?')


def midi_read_inputs():
    if len(midi_devices_connected) > 0:
        for device in midi_devices_connected:
            # TODO: Check if device still exists. device.closed does not do this
            for msg in device.iter_pending():
                if msg.type not in ['control_change', 'note_on', 'note_off']:
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
    global last_midi_input, midi_bindings
    if midiwindow != None:
        last_midi_input = bind
        midiwindow.write_event_value('Exit', None)
        save_binding()


def save_binding():
    global last_midi_input, midi_bindings
    if last_midi_input == None:
        return

    bind = None
    exists = -1

    for i in range(len(midi_bindings)):
        if midi_bindings[i].equals(last_midi_input):
            exists = i
            bind = midi_bindings[i]

    if exists == -1:
        bind = deepcopy(last_midi_input)
        midi_bindings.append(bind)
        config_append_binding(bind)
    else:
        config_update_binding(bind)

    mainwindow['_bindingtable_'].update(
        values=map(Binding.toArray, midi_bindings))

    rowNum = exists if exists > -1 else len(midi_bindings)-1

    mainwindow['_bindingtable_'].update(select_rows=[rowNum])
    mainwindow['_bindingtable_'].Widget.see(rowNum+1)


def update_binding(index):
    global actionwindow, midi_bindings

    row = index[0]
    column = index[1]

    if column == 4:
        # update Action
        actionstring = midi_bindings[row].actions
        actionwindow = make_actionwindow(row, actionstring)
        actionwindow['_actionstring_'].Widget.focus()
        actionwindow['_actionstring_'].Widget.select_range(0, 'end')
        actionwindow['_actionstring_'].Widget.icursor('end')


def update_action(index, value):
    bind = midi_bindings[index]
    bind.actions = value
    config_update_binding(bind)
    mainwindow['_bindingtable_'].update(
        values=map(Binding.toArray, midi_bindings))


midi_init()

# -----------------------------------------------------------
# Main loop

while True:
    midi_read_inputs()

    window, event, values = sg.read_all_windows(timeout=20)

    if event == sg.WIN_CLOSED or event == 'Exit':
        window.close()
        if window == actionwindow:
            actionwindow = None
        if window == midiwindow:
            midiwindow = None
        elif window == mainwindow:
            break
    elif event == '_devicelist_+-double click-':
        midi_connect(
            midi_devices_detected[mainwindow['_devicelist_'].GetIndexes()[0]])
    elif event == 'Refresh':
        midi_init()
    elif event == '_autoconnectmidi_':
        config.update({'midi_auto_connect': values['_autoconnectmidi_']})
    elif event == '_oscoutip_':
        config.update({'osc_ip': values['_oscoutip_']})
    elif event == '_oscoutport_':
        config.update({'osc_port': values['_oscoutport_']})
    elif event == 'Save settings':
        save_config()
    elif event == 'New Binding':
        if midiwindow == None:
            midiwindow = make_midiwindow()
        else:
            midiwindow.force_focus()
    elif event[0] == '_bindingtable_':
        last_clicked_cell = event[2]
    elif event == '_bindingtable_+-double click-':
        update_binding(last_clicked_cell)
    elif event == '_UpdateAction_':
        update_action(int(values['_actionrow_']), values['_actionstring_'])
        actionwindow.write_event_value('Exit', None)
    # elif event != '__TIMEOUT__':
    #     print(event)

# -----------------------------------------------------------
# End of main loop

mainwindow.close()
