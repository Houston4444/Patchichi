

import json
import logging
import operator
from pathlib import Path
from sqlite3 import connect
from typing import TYPE_CHECKING, Any, Optional, Union

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from patchbay.base_elements import (
    Connection, GroupPos, JackPortFlag, Port, PortgroupMem, Group)
from patchbay import (
    CanvasMenu,
    Callbacker,
    CanvasOptionsDialog,
    PatchbayManager,
    patchcanvas)
from patchbay.patchbay_manager import JACK_METADATA_ICON_NAME, JACK_METADATA_ORDER, JACK_METADATA_PORT_GROUP, JACK_METADATA_PRETTY_NAME, later_by_batch
from patchbay.patchcanvas.init_values import PortMode, PortType
from patchbay.patchcanvas.patchcanvas import add_port

from tools import get_code_root
import xdg

if TYPE_CHECKING:
    from main_win import MainWindow
    from patchichi import Main

_logger = logging.getLogger(__name__)

MEMORY_FILE = 'canvas.json'


class PatchichiCallbacker(Callbacker):
    def __init__(self, manager: 'PatchichiPatchbayManager'):
        super().__init__(manager)

        if TYPE_CHECKING:
            self.mng = manager
        
    def _ports_connect(self, group_out_id: int, port_out_id: int,
                       group_in_id: int, port_in_id: int):
        port_out = self.mng.get_port_from_id(group_out_id, port_out_id)
        port_in = self.mng.get_port_from_id(group_in_id, port_in_id)
        self.mng.add_connection(port_out.full_name, port_in.full_name)

    def _ports_disconnect(self, connection_id: int):
        for conn in self.mng.connections:
            if conn.connection_id == connection_id:
                self.mng.remove_connection(
                    conn.port_out.full_name, conn.port_in.full_name)
                break

class PatchichiPatchbayManager(PatchbayManager):
    main_win: 'MainWindow'
    
    def __init__(self, settings: Union[QSettings, None] =None):
        super().__init__(settings)
        self._settings = settings
        
        self.jack_mng = None
        self._memory_path = None
        self._last_active_lines = list[str]()
        self._gp_client_icons = dict[str, str]()
        
        if settings is not None:
            self._memory_path = Path(
                settings.fileName()).parent.joinpath(MEMORY_FILE)

            try:
                with open(self._memory_path, 'r') as f:                
                    json_dict = json.load(f)
                    assert isinstance(json_dict, dict)
            except FileNotFoundError:
                _logger.warning(f"File {self._memory_path} has not been found,"
                                "It is probably the first startup.")
                return
            except:
                _logger.warning(f"File {self._memory_path} is incorrectly written"
                                "it will be ignored.")
                return
            
            if 'group_positions' in json_dict.keys():
                gposs = json_dict['group_positions']

                for gpos in gposs:
                    if isinstance(gpos, dict):
                        self.group_positions.append(
                            GroupPos.from_serialized_dict(gpos))
            
            if 'portgroups' in json_dict.keys():
                pg_mems = json_dict['portgroups']

                for pg_mem_dict in pg_mems:
                    self.portgroups_memory.append(
                        PortgroupMem.from_serialized_dict(pg_mem_dict))
    
    def _setup_canvas(self):
        SUBMODULE = 'HoustonPatchbay'
        THEME_PATH = Path(SUBMODULE) / 'themes'
        source_theme_path = Path(get_code_root()) / THEME_PATH
        theme_paths = list[Path]()
        
        app_title = QApplication.applicationName().lower()
        
        theme_paths.append(xdg.xdg_data_home() / app_title / THEME_PATH)

        if source_theme_path.exists():
            theme_paths.append(source_theme_path)

        for p in xdg.xdg_data_dirs():
            path = p / app_title / THEME_PATH
            if path not in theme_paths:
                theme_paths.append(path)

        self.app_init(self.main_win.ui.graphicsView,
                      theme_paths,
                      callbacker=PatchichiCallbacker(self),
                      default_theme_name='Yellow Boards')

    def refresh(self):
        super().refresh()
    
    def update_from_text(self, text: str):
        def _log(string: str):
            _logger.warning(f'line {line_n}:{string}')
            log_lines.append(f'line {line_n} : {string}')

        def _is_gp(s: str) -> bool:
            return bool(s.startswith('::') and len(s) >= 3)

        active_lines = [l for l in text.splitlines() if l]

        ports_to_rename = list[tuple[str, str]]()
        group_to_rename: Optional[tuple[str, str]] = None
        full_modif = True

        if len(active_lines) == len(self._last_active_lines):
            full_modif = False
            group_name = ''
            
            for n in range(len(active_lines)):
                if _is_gp(active_lines[n]):
                    group_name = active_lines[n][2:]
                
                if active_lines[n] == self._last_active_lines[n]:
                    if (group_to_rename is not None
                            and group_name == group_to_rename[0]
                            and not active_lines[n].startswith(':')):
                        ports_to_rename.append(
                            f"{group_to_rename[0]}:{active_lines[n]}",
                            f"{group_to_rename[1]}:{active_lines[n]}")
                    continue

                # here the two compared lines are different

                if group_to_rename is not None:
                    # we can rename one group only
                    # if there is only its definition line changed.
                    full_modif = True
                    break

                if _is_gp(active_lines[n]):
                    if _is_gp(self._last_active_lines[n]):
                        if ports_to_rename:
                            full_modif = True
                            break

                        # remember the group to rename
                        group_to_rename = (self._last_active_lines[n][2:],
                                           active_lines[n][2:])
                    else:
                        full_modif = True
                        break

                elif (active_lines[n].startswith(':')
                        or self._last_active_lines[n].startswith(':')):
                    # parameter changed
                    full_modif = True
                    break
                else:
                    if not group_name:
                        full_modif = True
                        break

                    ports_to_rename.append(
                        (f"{group_name}:{self._last_active_lines[n]}",
                         f"{group_name}:{active_lines[n]}")
                    )
            
            if not full_modif:
                if not (ports_to_rename or group_to_rename):
                    # nothing really changed in the text
                    return
        
            # if not full_modif and (ports_to_rename or group_to_rename):

                if group_to_rename is not None:
                    print('oupsaa', group_to_rename)
                    old_gp_name, new_gp_name = group_to_rename
                    for gpos in self.group_positions:
                        if gpos.group_name == old_gp_name:
                            gpos.group_name = new_gp_name
                
                    group = self.get_group_from_name(old_gp_name)
                    if group is not None:
                        ports_to_add = list[tuple[str, int, int, int]]()
                        conns_to_remove = list[Connection]()
                        conns_to_add = list[tuple[str, str]]()
                        
                        for port in group.ports:
                            new_port_name = \
                                f"{new_gp_name}:{port.full_name.partition(':')[2]}"

                            ports_to_add.append((
                                new_port_name,
                                port.type.value, port.flags, port.uuid))

                            if port.mode() is PortMode.OUTPUT:
                                for conn in self.connections:
                                    if (conn.port_out is port
                                            and not conn in conns_to_remove):
                                        conns_to_remove.append(conn)

                                        if conn.port_in in group.ports:
                                            conns_to_add.append(
                                                (new_port_name,
                                                 f"{new_gp_name}:{conn.port_in.full_name.partition(':')[2]}")
                                            )
                                        else:
                                            conns_to_add.append(
                                                (new_port_name,
                                                 conn.port_in.full_name))

                            elif port.mode() is PortMode.INPUT:
                                for conn in self.connections:
                                    if (conn.port_in is port
                                            and not conn in conns_to_remove):
                                        conns_to_remove.append(conn)
                                        if conn.port_out in group.ports:
                                            conns_to_add.append(
                                                (f"{new_gp_name}:{conn.port_out.full_name.   partition(':')[2]}",
                                                 new_port_name)
                                            )
                                        else:
                                            conns_to_add.append(
                                                (conn.port_out.full_name,
                                                 new_port_name))
                        
                        self.optimize_operation(True)
                        
                        for conn in conns_to_remove:
                            conn.remove_from_canvas()
                            self.connections.remove(conn)
                            
                        group.remove_all_ports()
                        group.remove_from_canvas()
                        if group in self.groups:
                            self.groups.remove(group)
                        
                        self.very_fast_operation = True
                        
                        for port_name, port_type, flags, uuid in ports_to_add:
                            group_id = self.add_port(port_name, port_type, flags, uuid)

                        group = self.get_group_from_id(group_id)
                        if group is not None:
                            group.sort_ports_in_canvas()
                        
                        for port_out_name, port_in_name in conns_to_add:
                            self.add_connection(port_out_name, port_in_name)
                        
                        self.very_fast_operation = False
                        
                        if group is not None:
                            group.add_all_ports_to_canvas()
                        
                        for connection in self.connections:
                            connection.add_to_canvas()
                        
                        self.optimize_operation(False)
                        
                        if group is not None:
                            group.redraw_in_canvas()
                        else:
                            self.redraw_all_groups()
                        
                        # self.redraw_all_groups()

                elif ports_to_rename:
                    print('rogg', ports_to_rename)
                    for old_name, new_name in ports_to_rename:
                        self.rename_port(old_name, new_name)
                
                    # self.very_fast_operation = False
                    self.optimize_operation(False)
                    self.redraw_all_groups()
                self._last_active_lines.clear()
                self._last_active_lines = active_lines
                return
                

        log_lines = list[str]() 
        group_names_added = set[str]()
        groups_added = set[int]()
        line_n = 0
        group_name = ''
        gp_icon_name = ''
        group_uuid = 0
        portgroup = ''
        port_type = PortType.AUDIO_JACK
        port_mode = PortMode.OUTPUT
        port_flags = JackPortFlag.IS_OUTPUT
        port_uuid = 0

        added_ports = set[str]()
        tuple_conns = [(c.port_out.full_name, c.port_in.full_name)
                       for c in self.connections]
        self.clear_all()
        self.optimize_operation(True)
        self.very_fast_operation = True
        
        group_guis = dict[str, bool]()
        
        for line in text.splitlines():
            line_n += 1
            
            if not line.strip():
                continue
            
            if line.startswith('::'):
                tmp_group_name = line[2:]
                if tmp_group_name in group_names_added:
                    _log(f'"{tmp_group_name}" group has been already added !!!')
                    continue

                group_name = tmp_group_name
                portgroup = ''
                gp_icon_name = ''
                port_type = PortType.AUDIO_JACK
                port_mode = PortMode.OUTPUT
                port_flags = 0

            elif line.startswith(':'):
                params = line[1:].split(':')
                for param in params:
                    if param == 'AUDIO':
                        port_type = PortType.AUDIO_JACK
                        port_flags &= ~JackPortFlag.IS_CONTROL_VOLTAGE
                    elif param == 'MIDI':
                        port_type = PortType.MIDI_JACK
                        port_flags &= ~JackPortFlag.IS_CONTROL_VOLTAGE
                    elif param == 'CV':
                        port_type = PortType.AUDIO_JACK
                        port_flags |= JackPortFlag.IS_CONTROL_VOLTAGE
                    elif param == 'OUTPUT':
                        port_mode = PortMode.OUTPUT
                    elif param == 'INPUT':
                        port_mode = PortMode.INPUT
                    elif param == 'MONITOR':
                        port_flags |= JackPortFlag.CAN_MONITOR
                    elif param == 'TERMINAL':
                        port_flags |= JackPortFlag.IS_TERMINAL
                    elif param == 'PHYSICAL':
                        port_flags |= JackPortFlag.IS_PHYSICAL
                    elif param == '~PHYSICAL':
                        port_flags &= ~JackPortFlag.IS_PHYSICAL

                    elif param.startswith('PORTGROUP='):
                        portgroup = param.partition('=')[2]
                    elif param == '~PORTGROUP':
                        portgroup = ''

                    # after group params
                    elif param == 'GUI_HIDDEN':
                        group_guis[group_name] = False
                    elif param == 'GUI_VISIBLE':
                        group_guis[group_name] = True
                    elif param.startswith('CLIENT_ICON='):
                        self._gp_client_icons[group_name] = param.rpartition('=')[2]
                    elif param.startswith('ICON_NAME='):
                        gp_icon_name = param.partition('=')[2]

                    # after port params
                    elif param.startswith('PORT_ORDER='):
                        if not port_uuid:
                            _log('PORT_ORDER affected to no port')
                            continue
                        
                        port_order = param.partition('=')[2]
                        if not port_order.isdigit():
                            _log('PORT_ORDER {port_order} is not digits')
                            continue
                        
                        self.metadata_update(port_uuid, JACK_METADATA_ORDER, port_order)
                    
                    elif param.startswith('PRETTY_NAME='):
                        if not port_uuid:
                            _log('PRETTY_NAME affected to no port')
                            continue
  
                        self.metadata_update(
                            port_uuid,
                            JACK_METADATA_PRETTY_NAME,
                            param.partition('=')[2])
            else:
                if not group_name:
                    _log('No group name set')
                    continue
                
                full_port_name = f"{group_name}:{line}"
                if full_port_name in added_ports:
                    _log(f'Port "{full_port_name}" is already present !')
                    continue

                added_ports.add(full_port_name)

                port_uuid += 1
                group_id = self.add_port(
                    f'{group_name}:{line}',
                    port_type.value,
                    int(port_flags | port_mode),
                    port_uuid)
                
                if group_id not in groups_added:
                    groups_added.add(group_id)
                    group_uuid += 1
                    self.set_group_uuid_from_name(group_name, group_uuid)

                    if gp_icon_name:
                        self.metadata_update(
                            group_uuid,
                            JACK_METADATA_ICON_NAME,
                            gp_icon_name)

                if portgroup:
                    self.metadata_update(
                        port_uuid,
                        JACK_METADATA_PORT_GROUP,
                        portgroup)
        
        for group in self.groups:
            visible = group_guis.get(group.name)
            if visible is not None:
                group.set_optional_gui_state(visible)
         
        for group in self.groups:
            group.sort_ports_in_canvas()
         
        for port_out_full_name, port_in_full_name in tuple_conns:
            if (port_out_full_name in added_ports
                    and port_in_full_name in added_ports):
                self.add_connection(port_out_full_name, port_in_full_name)
        
        self.very_fast_operation = False

        for group in self.groups:
            group.add_all_ports_to_canvas()
        
        for connection in self.connections:
            connection.add_to_canvas()
                
        self.optimize_operation(False)        
        self.redraw_all_groups()
        
        self._last_active_lines.clear()
        self._last_active_lines = active_lines
        
        self.main_win.set_logs_text('\n'.join(log_lines))
    
    def export_port_list(self) -> str:
        def slcol(input_str: str) -> str:
            return input_str.replace(':', '\\:')
        
        contents = ''
        
        gps_and_ports = list[tuple[str, list[Port]]]()
        for group in self.groups:
            for port in group.ports:
                group_name = port.full_name.partition(':')[0]
                for gp_name, gp_port_list in gps_and_ports:
                    if gp_name == group_name:
                        gp_port_list.append(port)
                        break
                else:
                    gps_and_ports.append((group_name, [port]))

        for group_name, port_list in gps_and_ports:
            port_list.sort(key=operator.attrgetter('port_id'))
                
        for group_name, port_list in gps_and_ports:
            gp_written = False              
            last_type_and_mode = (PortType.NULL, PortMode.NULL)
            physical = False
            pg_name = ''

            for port in port_list:
                if not gp_written:
                    contents += f'\n::{group_name}\n'
                    gp_written = True

                    group = self.get_group_from_name(group_name)
                    if group is not None:
                        group_attrs = list[str]()
                        if group.client_icon:
                            group_attrs.append(f'CLIENT_ICON={slcol(group.client_icon)}')
                            
                        if group.mdata_icon:
                            group_attrs.append(f'ICON_NAME={slcol(group.mdata_icon)}')

                        if group.has_gui:
                            if group.gui_visible:
                                group_attrs.append('GUI_VISIBLE')
                            else:
                                group_attrs.append('GUI_HIDDEN')
                        if group_attrs:
                            contents += ':'
                            contents += ':'.join(group_attrs)

                if port.flags & JackPortFlag.IS_PHYSICAL:
                    if not physical:
                        contents += ':PHYSICAL\n'
                        physical = True
                elif physical:
                    contents += ':~PHYSICAL\n'
                    physical = False

                if last_type_and_mode != (port.type, port.mode()):
                    if port.type is PortType.AUDIO_JACK:
                        if port.flags & JackPortFlag.IS_CONTROL_VOLTAGE:
                            contents += ':CV'
                        else:
                            contents += ':AUDIO'
                    elif port.type is PortType.MIDI_JACK:
                        contents += ':MIDI'

                    contents += f':{port.mode().name}\n'
                    last_type_and_mode = (port.type, port.mode())
                
                if port.mdata_portgroup != pg_name:
                    if port.mdata_portgroup:
                        contents += f':PORTGROUP={slcol(port.mdata_portgroup)}\n'
                    else:
                        contents += ':~PORTGROUP\n'
                    pg_name = port.mdata_portgroup

                port_short_name = port.full_name.partition(':')[2]
                contents += f'{port_short_name}\n'
                
                if port.pretty_name or port.order:
                    port_attrs = list[str]()
                    if port.pretty_name:
                        port_attrs.append(f'PRETTY_NAME={slcol(port.pretty_name)}')
                    if port.order:
                        port_attrs.append(f'PORT_ORDER={port.order}')
                    contents += '\n'
                    contents += ':'.join(port_attrs)

        return contents

    def get_existing_connections(self) -> list[tuple[str, str]]:
        return_list = list[tuple[str, str]]()
        for conn in self.connections:
            return_list.append(
                (conn.port_out.full_name, conn.port_in.full_name))
        return return_list
    
    def get_existing_positions(self) -> list[GroupPos]:
        return [gpos for gpos in self.group_positions
                if gpos.group_name in [g.name for g in self.groups]]

    @later_by_batch()
    def rewrite_connections_text(self):
        conns_dict = dict[str, list[str]]()
        
        for conn in self.connections:
            out_list = conns_dict.get(conn.port_out.full_name)
            if out_list is None:
                conns_dict[conn.port_out.full_name] = [conn.port_in.full_name]
            else:
                out_list.append(conn.port_in.full_name)
        
        contents = ''    
            
        for port_out, ports_in in conns_dict.items():
            contents += f"{port_out}\n"
            for port_in in ports_in:
                contents += f":> {port_in}\n"
        
        self.main_win.set_logs_text(contents)
        
        print(self.export_port_list())
        print(self.get_existing_connections())
        print(self.get_existing_positions())
    
    def set_group_as_nsm_client(self, group: Group):
        icon_name = self._gp_client_icons.get(group.name)
        if icon_name is not None:
            group.client_icon = icon_name
            if '.' in group.name:
                group.display_name = group.name.partition('.')[2]

    def finish_init(self, main: 'Main'):
        self.set_main_win(main.main_win)
        self._setup_canvas()

        self.set_canvas_menu(CanvasMenu(self))
        self.set_tools_widget(main.main_win.patchbay_tools)
        self.set_filter_frame(main.main_win.ui.filterFrame)
        self.set_options_dialog(
            CanvasOptionsDialog(self.main_win, self, self._settings))
        
        # prevent 'Jack is not running' red label to be displayed
        self.server_started()

    def save_positions(self):        
        gposs_as_dicts = [gpos.as_serializable_dict()
                          for gpos in self.group_positions]
        pg_mems_as_dict = [pg_mem.as_serializable_dict()
                           for pg_mem in self.portgroups_memory]
        
        full_dict = {'group_positions': gposs_as_dicts,
                     'portgroups': pg_mems_as_dict}
        
        if self._memory_path is not None:
            try:
                with open(self._memory_path, 'w') as f:
                    json.dump(full_dict, f, indent=4)
            except Exception as e:
                _logger.warning(str(e))
                
    def save_file_to(self, path: Path) -> bool:
        file_dict = dict[str, Any]()
        
        editor_text = self.main_win.get_editor_text()
        
        for gpos in self.group_positions:
            print('gpos:', gpos.group_name, gpos.flags)
        
        file_dict['editor_text'] = editor_text
        conn_list = list[tuple[str, str]]()
        for conn in self.connections:
            conn_list.append(
                (conn.port_out.full_name, conn.port_in.full_name))
        file_dict['connections'] = conn_list
        file_dict['group_positions'] = [
            gpos.as_serializable_dict() for gpos in self.group_positions
            if self.get_group_from_name(gpos.group_name) is not None]
        
        portgroups = list[dict[str, Any]]()
        for pg_mem in self.portgroups_memory:
            group = self.get_group_from_name(pg_mem.group_name)
            if group is None:
                continue

            for port_str in pg_mem.port_names:
                for port in group.ports:
                    if (port.short_name() == port_str
                            and port.type() == pg_mem.port_type
                            and port.mode() == pg_mem.port_mode):
                        portgroups.append(pg_mem.as_serializable_dict())
                        break
        
        file_dict['portgroups'] = portgroups

        try:
            with open(path, 'w') as f:
                json.dump(file_dict, f, indent=2)
            return True
        except Exception as e:
            _logger.error(f'Failed to save patchichi file: {str(e)}')
            return False

    def load_file(self, path: Path) -> bool:
        try:
            with open(path, 'r') as f:
                json_dict = json.load(f)
                assert isinstance(json_dict, dict)
        except Exception as e:
            _logger.error(f'Failed to open file "{str(Path)}", {str(e)}')
            return False

        editor_text: str = json_dict['editor_text']
        connections: list[tuple[str, str]] = json_dict['connections']
        group_positions: list[dict] = json_dict['group_positions']
        portgroups: list[dict] = json_dict['portgroups']

        self.clear_all()

        self.group_positions.clear()
        self.portgroups_memory.clear()

        for gpos_dict in group_positions:
            self.group_positions.append(
                GroupPos.from_serialized_dict(gpos_dict))

        for gpos in self.group_positions:
            print('gposin', gpos.port_types_view, gpos.group_name, gpos.flags)

        for gp_mem_dict in portgroups:
            self.portgroups_memory.append(
                PortgroupMem.from_serialized_dict(gp_mem_dict))

        self.main_win.ui.plainTextEditPorts.setPlainText(editor_text)
        for port_out_name, port_in_name in connections:
            self.add_connection(port_out_name, port_in_name)

        return True

