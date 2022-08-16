from enum import Enum


class Binding:
    def __init__(self, device_name, voice, channel, address, actions=[], value=0):
        self.device_name = device_name    # E.g. Akai APC 40 0
        self.voice = voice                # Usually note_on, note_off or control_change
        self.channel = int(channel)
        self.address = int(address)            # Note or control no.
        self.value = value                # Control value or note velocity
        self.actions = actions

    def equals(self, other):
        return (
            self.device_name == other.device_name and
            self.voice == other.voice and
            self.channel == other.channel and
            self.address == other.address
        )

    @staticmethod
    def toArray(bind):
        return [
            bind.device_name,
            bind.voice,
            str(bind.channel),
            str(bind.address),
            ', '.join(map(Action.toString, bind.actions))
        ]

    @staticmethod
    def fromDict(d):
        return Binding(
            device_name=d['device'],
            voice=d['voice'],
            channel=d['channel'],
            address=d['address'],
            actions=list(map(Action.fromDict, d['actions']))
        )


class Action:
    def __init__(self,
                 action_message='',
                 osc_values={'low': 0, 'high': 1}):
        self.action_message = action_message
        self.osc_values = osc_values

    @staticmethod
    def toString(action):
        return action.action_message

    @staticmethod
    def toDict(action):
        return {'message': action.action_message, 'values': action.osc_values}

    @staticmethod
    def fromDict(d):
        print(d['message'])
        return Action(
            action_message=d['message'],
            osc_values=d['values']
        )
