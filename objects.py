from enum import Enum


class Binding:
    def __init__(self, device_name, voice, channel, address, actions='', value=0, send_note_off=False, is_encoder=False):
        self.device_name = device_name    # E.g. Akai APC 40 0
        self.voice = voice                # Usually note_on, note_off or control_change
        self.channel = int(channel)
        self.address = int(address)       # Note or control no.
        self.value = value                # Control value or note velocity
        self.actions = actions
        self.send_note_off = send_note_off or False
        self.is_encoder = is_encoder or False

    def equals(self, other):
        return (
            self.device_name == other.device_name and
            self.voice[0:4] == other.voice[0:4] and
            self.channel == other.channel and
            self.address == other.address
        )

    def __str__(self):
        return "device: " + self.device_name + \
            " voice: " + self.voice + \
            " channel: " + str(self.channel) + \
            " address: " + str(self.address) + \
            " value: " + str(self.value) + \
            " actions: " + self.actions + \
            " send note off: " + self.send_note_off + \
            " is encoder: " + self.is_encoder

    @staticmethod
    def toArray(bind):
        return [
            bind.device_name,
            bind.voice,
            str(bind.channel),
            str(bind.address),
            bind.actions,
            bind.send_note_off,
            bind.is_encoder
        ]

    @staticmethod
    def fromDict(d):
        return Binding(
            device_name=d.get('device'),
            voice=d.get('voice'),
            channel=d.get('channel'),
            address=d.get('address'),
            actions=d.get('actions'),
            send_note_off=d.get('send_note_off'),
            is_encoder=d.get('is_encoder')
        )
