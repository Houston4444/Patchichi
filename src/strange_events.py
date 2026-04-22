import time
from typing import TYPE_CHECKING

from patshared import PortType

from patchbay.bases.elements import JackPortFlag
from patshared import JackMetadata

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
    
def set_cv_later(mng: 'PatchichiPatchbayManager'):
    mng.add_port('bonojour:audio_va_cv_out', PortType.AUDIO_JACK,
                 JackPortFlag.IS_OUTPUT, 7984212)
    time.sleep(1.0)
    mng.add_connection('bonojour:audio_va_cv_out', 'Ardour:Master/audio_in 1')
    time.sleep(1.0)
    mng.metadata_update(7984212, JackMetadata.SIGNAL_TYPE, 'CV')

def folayage_cv(mng: 'PatchichiPatchbayManager'):
    grp = 'Souris'
    uuid_min = 100000
    for kk in range(10):
        for i in range(16):
            mng.add_port(f'{grp}:audio_out_{i+1}', PortType.AUDIO_JACK,
                        JackPortFlag.IS_OUTPUT, uuid_min + i)
            mng.add_port(f'{grp}:audio_in_{i+1}', PortType.AUDIO_JACK,
                        JackPortFlag.IS_INPUT, uuid_min + i + 16)
            
            if i < 4:
                mng.metadata_update(uuid_min + i, JackMetadata.PORT_GROUP, 'toudanlmem')
            mng.metadata_update(uuid_min + i, JackMetadata.ORDER, str((i + 2) % 16))
        # time.sleep(0.060)
        if kk != 9:
            for i in range(16):
                mng.remove_port(f'{grp}:audio_out_{i+1}')
                mng.remove_port(f'{grp}:audio_in_{i+1}')
            # time.sleep(0.040)
        print('tour', kk)
    
    # mng.metadata_update(100000, JackMetadata.SIGNAL_TYPE, 'CV')
    # mng.metadata_update(100001, JackMetadata.SIGNAL_TYPE, 'CV')
    
    
    
    # for i in range(16):
    #     mng.rename_port(f'{grp}:audio_out_{i+1}', f'{grp}:audio_out_{i+2}')

def create_connect(mng: 'PatchichiPatchbayManager'):
    uuid_min = 110000
    for i in range(1, 3):
        mng.add_port(
            f'Tatar:audio_out_{i}', PortType.AUDIO_JACK, JackPortFlag.IS_OUTPUT, uuid_min+i)
        mng.add_port(
            f'Toutoux:audio_in_{i}', PortType.AUDIO_JACK, JackPortFlag.IS_INPUT, uuid_min + 2 +i)
        mng.add_connection(f'Tatar:audio_out_{i}', f'Toutoux:audio_in_{i}')

def remove_master(mng: 'PatchichiPatchbayManager'):
    mng.remove_port('Ardour:Master/audio_out 1')
    mng.remove_port('Ardour:Master/audio_out 2')
    mng.remove_port('Ardour:Master/audio_in 1')
    mng.remove_port('Ardour:Master/audio_in 2')
    # time.sleep(0.100)
    mng.add_port('Ardour:Masterax/audio_out 1', PortType.AUDIO_JACK, JackPortFlag.IS_OUTPUT, 456456)
    mng.add_port('Ardour:Masterax/audio_out 2', PortType.AUDIO_JACK, JackPortFlag.IS_OUTPUT, 456457)
    mng.add_port('Ardour:Masterax/audio_in 1',  PortType.AUDIO_JACK, JackPortFlag.IS_INPUT, 456458)
    mng.add_port('Ardour:Masterax/audio_in 2',  PortType.AUDIO_JACK, JackPortFlag.IS_INPUT, 456459)
    
def add_ardour_track(mng: 'PatchichiPatchbayManager'):
    mng.add_port('Ardour:Malisk/audio_out 1', PortType.AUDIO_JACK, JackPortFlag.IS_OUTPUT, 4564560)
    mng.add_port('Ardour:Malisk/audio_out 2', PortType.AUDIO_JACK, JackPortFlag.IS_OUTPUT, 4564561)
    mng.add_port('Ardour:Malisk/audio_in 1', PortType.AUDIO_JACK, JackPortFlag.IS_INPUT, 4564562)
    mng.add_port('Ardour:Malisk/audio_in 2', PortType.AUDIO_JACK, JackPortFlag.IS_INPUT, 4564563)
    
def rename_master(mng: 'PatchichiPatchbayManager'):
    port = mng.get_port_from_name('Ardour:Master/audio_out 1')
    if port is None:
        return
    mng.rename_port('Ardour:Master/audio_out 1', 'Ardour:NewMaster/audio_out 1')
    mng.rename_port('Ardour:Master/audio_out 2', 'Ardour:NewMaster/audio_out 2')
    mng.rename_port('Ardour:Master/audio_in 1', 'Ardour:NewMaster/audio_in 1')
    mng.rename_port('Ardour:Master/audio_in 2', 'Ardour:NewMaster/audio_in 2')
    # mng.rename_port('Ardour:NewMaster/audio_out 1', 'Ardour:Master/audio_out 1')
    # mng.rename_port('Ardour:NewMaster/audio_out 2', 'Ardour:Master/audio_out 2')
    
def portgroup_track(mng: 'PatchichiPatchbayManager'):
    mng.add_port('Ardour:Mouslo_L/audio_out 1', PortType.AUDIO_JACK, JackPortFlag.IS_OUTPUT, 987987)
    mng.add_port('Ardour:Mouslo_R/audio_out 1', PortType.AUDIO_JACK, JackPortFlag.IS_OUTPUT, 987988)
    mng.metadata_update(987987, JackMetadata.PORT_GROUP, 'Mouslo')
    mng.metadata_update(987987, JackMetadata.ORDER, '97')
    mng.metadata_update(987988, JackMetadata.PORT_GROUP, 'Mouslo')
    mng.metadata_update(987988, JackMetadata.ORDER, '98')