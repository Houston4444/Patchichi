import time
from typing import TYPE_CHECKING

from patshared import PortType

from patchbay.bases.elements import JackPortFlag

if TYPE_CHECKING:
    from patchichi_pb_manager import PatchichiPatchbayManager
    

def special_act_12(mng: 'PatchichiPatchbayManager'):
    mng.add_port('Ardour:slip/audio_out 1', PortType.AUDIO_JACK,
                 JackPortFlag.IS_OUTPUT, 148987)
    mng.add_port('Ardour:slip/audio_out 2', PortType.AUDIO_JACK,
                 JackPortFlag.IS_OUTPUT, 148988)
    time.sleep(1.0)
    mng.add_connection('Ardour:slip/audio_out 1', 'Ardour:Master/audio_in 1')
    mng.add_connection('Ardour:slip/audio_out 2', 'Ardour:Master/audio_in 2')

def special_act_34(mng: 'PatchichiPatchbayManager'):
    mng.add_port('Ardour:slip/audio_out 3', PortType.AUDIO_JACK,
                 JackPortFlag.IS_OUTPUT, 148987)
    mng.add_port('Ardour:slip/audio_out 4', PortType.AUDIO_JACK,
                 JackPortFlag.IS_OUTPUT, 148988)
    time.sleep(1.0)
    mng.add_connection('Ardour:slip/audio_out 3', 'Ardour:Master/audio_in 1')
    mng.add_connection('Ardour:slip/audio_out 4', 'Ardour:Master/audio_in 2')
    
def manger_bio_88(mng: 'PatchichiPatchbayManager'):
    mng.add_port('Koukou:comme_grenade_in_1', PortType.MIDI_JACK,
                 JackPortFlag.IS_INPUT, 1654788)