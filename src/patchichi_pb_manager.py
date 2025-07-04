

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from qtpy.QtCore import QSettings
from qtpy.QtWidgets import QApplication

from patshared import (
    PortMode, PortType, PortTypesViewFlag, JackMetadata)
from patchbay.bases.elements import CanvasOptimize, CanvasOptimizeIt, JackPortFlag
from patchbay import (
    CanvasMenu,
    Callbacker,
    CanvasOptionsDialog,
    PatchbayManager,
    Group)

from patchbay.tools_widgets import JackAgnostic

from chichi_syntax import split_params
import xdg

if TYPE_CHECKING:
    from main_win import MainWindow
    from patchichi import Main


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

MEMORY_FILE = 'canvas.json'


class RenameBuffer:
    '''This serves for group or port renaming
    with the editor. This is only used when the group name
    or the port name becomes empty.

    If one and only one line has changed since last update,
    connections, group positions and portgroups memories
    will be renamed'''
    def __init__(self, line: int, old: str, gp_name=''):
        self.line = line
        self.old = old
        self.conns = list[tuple[str, str]]()
        self.portgroups = list[tuple[str, str]]()
        
        # gp_name is used for port rename
        self.gp_name = gp_name
        
    def renamed_conns(self, new_name: str) -> list[tuple[str, str]]:
        out_list = list[tuple[str, str]]()
        
        if not self.gp_name:
            # This is a group renamer
            new_gp_name = new_name
            for out_p, in_p in self.conns:
                if out_p.startswith(self.old + ':'):
                    out_p = new_gp_name + ':' + out_p.partition(':')[2]
                if in_p.startswith(self.old + ':'):
                    in_p = new_gp_name + ':' + in_p.partition(':')[2]
                
                out_list.append((out_p, in_p))
        
        else:
            # This is a port renamer
            new_p_name = new_name
            for out_p, in_p in self.conns:
                if out_p == self.gp_name + ':' + self.old:
                    out_p = self.gp_name + ':' + new_p_name
                if in_p == self.gp_name + ':' + self.old:
                    in_p = self.gp_name + ':' + new_p_name
                
                out_list.append((out_p, in_p))
        
        return out_list
    

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
            
    def _group_selected(self, group_id: int, splitted_mode: PortMode):
        group = self.mng.get_group_from_id(group_id)
        if group is None:
            return
        
        text_lines = self.mng.main_win.get_editor_text().splitlines()
        for i in range(len(text_lines)):
            line = text_lines[i]
            if line == '::' + group.name:
                self.mng.main_win.ui.plainTextEditPorts.move_cursor_to_line(i)
                break
        else:
            # this works to find a2j or MidiBridge groups when they are in
            # not grouped mode.
            if not group.ports:
                return

            port = group.ports[0]
            gp_name = port.full_name.partition(':')[0]
            for i in range(len(text_lines)):
                line = text_lines[i]
                if line == '::' + gp_name:
                    self.mng.main_win.ui.plainTextEditPorts.move_cursor_to_line(i)
                    break
            
            


class PatchichiPatchbayManager(PatchbayManager):
    main_win: 'MainWindow'
    
    def __init__(self, settings: Union[QSettings, None] =None):
        super().__init__(settings)
        self._settings = settings
        
        self.jack_mng = None
        self._memory_path = None
        self._last_text_lines = list[str]()
        self._gp_client_icons = dict[str, str]()
        
        # Used to remember group position and connections
        # if a group is renamed (changing only its line definition),
        # it is only used when the group name is set to empty
        self._rename_buffer: Optional[RenameBuffer] = None
        self._prevent_next_editor_update = False
    
    def _setup_canvas(self):
        SUBMODULE = 'HoustonPatchbay'
        THEME_PATH = Path(SUBMODULE) / 'themes'
        source_theme_path = Path(__file__).parents[1] / THEME_PATH
        manual_path = Path(__file__).parents[1] / SUBMODULE / 'manual'
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
                      manual_path=manual_path,
                      callbacker=PatchichiCallbacker(self),
                      default_theme_name='Yellow Boards')

    def refresh(self):
        self.update_from_text(
            self.main_win.ui.plainTextEditPorts.toPlainText())
    
    def _check_port_or_group_renaming(
            self, text: str) -> list[tuple[str, str]]:
        '''Checks if there is a group or a port renamed only in editor,
        renames group positions, portgroups, and connections,
        returns list of connections as tuple[str, str]'''

        group_renamed = tuple[str, str]()
        port_renamed = tuple[str, str, str]()
        tuple_conns = list[tuple[str, str]]()
        changed_line_n = -1
        gp_name = ''
        all_ports = set[str]()
        ignored_double_ports = set[str]()
        
        # we don't use splitlines() here, because it doesn't gives
        # the last line if it is empty.
        text_lines = text.split('\n')

        # check if there is only one line changed
        if len(text_lines) == len(self._last_text_lines):
            for n in range(len(text_lines)):
                if text_lines[n].startswith('::'):
                    gp_name = text_lines[n][2:]
                    all_ports.clear()
                    ignored_double_ports.clear()

                elif gp_name and not text_lines[n].startswith(':'):
                    # remember all ports
                    # to prevent double port declarations
                    if text_lines[n] in all_ports:
                        ignored_double_ports.add(text_lines[n])
                    all_ports.add(text_lines[n])

                if text_lines[n] != self._last_text_lines[n]:
                    if changed_line_n >= 0:
                        changed_line_n = -1
                        break
                    changed_line_n = n
        
        if changed_line_n == -1:
            # More than one line has changed
            self._last_text_lines = text_lines.copy()
            self._rename_buffer = None
            return [(c.port_out.full_name, c.port_in.full_name)
                    for c in self.connections]
        
        # One line only has changed.
        # If it is a group line definition,
        # we will first remember and modify group positions
        # and connections.
        old_text = self._last_text_lines[changed_line_n]
        new_text = text_lines[changed_line_n]

        self._last_text_lines = text_lines.copy()

        if old_text.startswith('::') and new_text.startswith('::'):
            # group is renamed
            old_group, new_group = old_text[2:], new_text[2:]
            if new_group and old_group:
                group_renamed = (old_group, new_group)

            elif new_group:
                rb = self._rename_buffer
                
                if (rb is not None
                        and rb.line == changed_line_n
                        and not rb.gp_name):
                    group_renamed = (rb.old, new_group)
                    tuple_conns.extend(rb.renamed_conns(new_group))

                self._rename_buffer = None

            elif old_group:                    
                rb = RenameBuffer(changed_line_n, old_group)
                for conn in self.connections:
                    out_p = conn.port_out.full_name
                    in_p = conn.port_in.full_name
                    
                    if (out_p.startswith(rb.old + ':')
                            or in_p.startswith(rb.old + ':')):
                        rb.conns.append((out_p, in_p))
                
                self._rename_buffer = rb
        
        elif (gp_name
                and not old_text.startswith(':')
                and not new_text.startswith(':')):
            # port is renamed
            old_p_name, new_p_name = old_text, new_text

            if old_p_name and new_p_name:
                if not new_p_name in ignored_double_ports:
                    port_renamed = (gp_name, old_p_name, new_p_name)

            elif new_p_name:
                rb = self._rename_buffer
                if (rb is not None
                        and rb.line == changed_line_n
                        and rb.gp_name == gp_name):
                    port_renamed = (gp_name, rb.old, new_p_name)
                    tuple_conns.extend(rb.renamed_conns(new_p_name))

            elif old_p_name:
                rb = RenameBuffer(changed_line_n, old_p_name, gp_name)
                for conn in self.connections:
                    out_p = conn.port_out.full_name
                    in_p = conn.port_in.full_name
                    
                    if gp_name + ':' + old_p_name in (out_p, in_p):
                        rb.conns.append((out_p, in_p))
                        
                self._rename_buffer = rb

        # remember (and rename) all connections.
        # in case of simple line renaming, 
        # remember also group positions and portgroups

        if group_renamed:
            for view_data in self.views.values():
                for ptv_dict in view_data.ptvs.values():
                    gpos = ptv_dict.get(group_renamed[0])
                    if gpos is not None:
                        gpos.group_name = group_renamed[1]
                        ptv_dict[group_renamed[1]] = \
                            ptv_dict.pop(group_renamed[0])
            
            for ptype_dict in self.portgroups_memory.values():
                if group_renamed[0] not in ptype_dict.keys():
                    continue

                ptype_dict[group_renamed[1]] = \
                    ptype_dict.pop(group_renamed[0])

                for pmode_list in ptype_dict[group_renamed[1]].values():
                    for pg_mem in pmode_list:
                            pg_mem.group_name = group_renamed[1]
            
            for conn in self.connections:
                out_p = conn.port_out.full_name
                in_p = conn.port_in.full_name
                
                if out_p.startswith(group_renamed[0] + ':'):
                    out_p = group_renamed[1] + ':' + out_p.partition(':')[2]
                if in_p.startswith(group_renamed[0] + ':'):
                    in_p = group_renamed[1] + ':' + in_p.partition(':')[2]

                tuple_conns.append((out_p, in_p))

        elif port_renamed:
            gp_name, old_p_name, new_p_name = port_renamed

            for ptype_dict in self.portgroups_memory.values():
                gp_dict = ptype_dict.get(gp_name)
                if gp_dict is None:
                    continue

                for pmode_list in gp_dict.values():
                    for pg_mem in pmode_list:
                        new_port_names = list[str]()
                        
                        for port_name in pg_mem.port_names:
                            if port_name == old_p_name:
                                port_name = new_p_name
                            
                            new_port_names.append(port_name)
                        pg_mem.port_names.clear()
                        pg_mem.port_names.extend(new_port_names)
            
            for conn in self.connections:
                out_p = conn.port_out.full_name
                in_p = conn.port_in.full_name
                
                if out_p == gp_name + ':' + old_p_name:
                    out_p = gp_name + ':' + new_p_name
                if in_p == gp_name + ':' + old_p_name:
                    in_p = gp_name + ':' + new_p_name
                    
                tuple_conns.append((out_p, in_p))
        else:
            tuple_conns = [(c.port_out.full_name, c.port_in.full_name)
                           for c in self.connections]
            
        return tuple_conns
    
    def update_from_text(self, text: str):
        def _log(string: str):
            _logger.warning(f'line {line_n}:{string}')
            log_lines.append(f'line {line_n} : {string}')

        if self._prevent_next_editor_update:
            self._prevent_next_editor_update = False
            return

        tuple_conns = self._check_port_or_group_renaming(text)

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
        
        # at each editor text modification
        # the patchbay elements are fully remade.
        
        self.clear_all()
        # self.optimize_operation(True)
        # self.very_fast_operation = True
        
        with CanvasOptimizeIt(self, CanvasOptimize.VERY_FAST):
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
                    elif not tmp_group_name:
                        _log(f" group name is empty !")

                    group_name = tmp_group_name
                    portgroup = ''
                    signal_type = ''
                    gp_icon_name = ''
                    port_type = PortType.AUDIO_JACK
                    port_mode = PortMode.OUTPUT
                    port_flags = 0

                elif line.startswith(':'):
                    for param, *args in split_params(line):
                        if param == 'AUDIO':
                            port_type = PortType.AUDIO_JACK
                            port_flags &= ~JackPortFlag.IS_CONTROL_VOLTAGE
                        elif param == 'MIDI':
                            port_type = PortType.MIDI_JACK
                            port_flags &= ~JackPortFlag.IS_CONTROL_VOLTAGE
                        elif param == 'CV':
                            port_type = PortType.AUDIO_JACK
                            port_flags |= JackPortFlag.IS_CONTROL_VOLTAGE
                        elif param == 'ALSA':
                            port_type = PortType.MIDI_ALSA
                            port_flags &= ~JackPortFlag.IS_CONTROL_VOLTAGE
                        elif param == 'VIDEO':
                            port_type = PortType.VIDEO
                            port_flags &= ~JackPortFlag.IS_CONTROL_VOLTAGE
                        elif param == 'OUTPUT':
                            port_mode = PortMode.OUTPUT
                        elif param == 'INPUT':
                            port_mode = PortMode.INPUT
                        elif param == 'MONITOR':
                            port_flags |= JackPortFlag.CAN_MONITOR
                        elif param == '~MONITOR':
                            port_flags &= ~JackPortFlag.CAN_MONITOR
                        elif param == 'TERMINAL':
                            port_flags |= JackPortFlag.IS_TERMINAL
                        elif param == '~TERMINAL':
                            port_flags &= ~JackPortFlag.IS_TERMINAL
                        elif param == 'PHYSICAL':
                            port_flags |= JackPortFlag.IS_PHYSICAL
                        elif param == '~PHYSICAL':
                            port_flags &= ~JackPortFlag.IS_PHYSICAL

                        elif param.startswith('PORTGROUP='):
                            portgroup = param.partition('=')[2]
                        elif param == '~PORTGROUP':
                            portgroup = ''

                        elif param.startswith('SIGNAL_TYPE='):
                            signal_type = param.partition('=')[2]
                        elif param == '~SIGNAL_TYPE':
                            signal_type = ''

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
                        elif param.startswith('ORDER='):
                            if not port_uuid:
                                _log('ORDER affected to no port')
                                continue
                            
                            port_order = param.partition('=')[2]
                            if not port_order.isdigit():
                                _log(f'ORDER "{port_order}" is not digits')
                                continue
                            
                            self.metadata_update(
                                port_uuid, JackMetadata.ORDER, port_order)
                        
                        elif param.startswith('PRETTY_NAME='):
                            if not port_uuid:
                                _log('PRETTY_NAME affected to no port')
                                continue
    
                            self.metadata_update(
                                port_uuid,
                                JackMetadata.PRETTY_NAME,
                                param.partition('=')[2])
                else:
                    if not group_name:
                        _log('No group name set')
                        continue
                    
                    full_port_name = f"{group_name}:{line}"
                    
                    if port_type is PortType.MIDI_ALSA:
                        if port_mode is PortMode.OUTPUT:
                            full_port_name = ":ALSA_OUT:0:0:" + full_port_name
                        else:
                            full_port_name = ":ALSA_IN:0:0:" + full_port_name

                    if full_port_name in added_ports:
                        _log(f'Port "{full_port_name}" is already present !')
                        continue

                    added_ports.add(full_port_name)

                    port_uuid += 1
                    group_id = self.add_port(
                        full_port_name,
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
                                JackMetadata.ICON_NAME,
                                gp_icon_name)

                    if portgroup:
                        self.metadata_update(
                            port_uuid,
                            JackMetadata.PORT_GROUP,
                            portgroup)
                        
                    if signal_type:
                        self.metadata_update(
                            port_uuid,
                            JackMetadata.SIGNAL_TYPE,
                            signal_type)
            
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

        with CanvasOptimizeIt(self, auto_redraw=True):
            for group in self.groups:
                group.add_to_canvas()
                group.add_all_ports_to_canvas()
            
            for connection in self.connections:
                connection.add_to_canvas()
        
        self.main_win.set_logs_text('\n'.join(log_lines))
    
    def set_group_as_nsm_client(self, group: Group):
        icon_name = self._gp_client_icons.get(group.name)
        if icon_name is not None:
            group.client_icon = icon_name
            if '.' in group.name:
                group.graceful_name = group.name.partition('.')[2]

    def select_port(self, full_port_name: str):
        port = self.get_port_from_name(full_port_name)
        if port is None:
            return

        port.select_in_canvas()

    def select_group(self, group_name: str):
        group = self.get_group_from_name(group_name)
        if group is None:
            return
        
        group.select_filtered_box(n_select=1)

    def finish_init(self, main: 'Main'):
        self.set_main_win(main.main_win)
        self._setup_canvas()

        self.set_canvas_menu(CanvasMenu(self))
        self.set_filter_frame(main.main_win.ui.filterFrame)
        main.main_win._tools_widgets.set_jack_agnostic(JackAgnostic.FULL)
        self.set_tools_widget(main.main_win._tools_widgets)
        self.set_options_dialog(
            CanvasOptionsDialog(self.main_win, self))
                
    def save_file_to(self, path: Path) -> bool:
        _logger.info(f'saving file {str(path)}')
        
        self.export_to_patchichi_json(
            path, self.main_win.get_editor_text())

    def load_file(self, path: Path) -> bool:
        try:
            with open(path, 'r') as f:
                json_dict = json.load(f)
                assert isinstance(json_dict, dict)
        except Exception as e:
            _logger.error(f'Failed to open file "{str(path)}", {str(e)}')
            return False

        self.portgroups_memory.clear()

        editor_text: str = json_dict.get('editor_text')
        connections: list[tuple[str, str]] = json_dict.get('connections')
        group_positions: list[dict] = json_dict.get('group_positions')
        self.views.eat_json_list(json_dict.get('views'), clear=True)
        self.portgroups_memory.eat_json(json_dict.get('portgroups'))
        version: tuple[int, int] = json_dict.get('version')

        _logger.info(f'Loading file {str(path)}')
            
        self.clear_all()

        for view_key in self.views.keys():
            # select the first view
            self.view_number = view_key
            break
        else:
            # no views in the file, write an empty view
            self.views.add_view(view_num=self.view_number)

        if (json_dict.get('views') is None
                and isinstance(group_positions, list)):
            higher_ptv_int = (PortTypesViewFlag.AUDIO
                              | PortTypesViewFlag.MIDI
                              | PortTypesViewFlag.CV).value

            for gpos_dict in group_positions:
                if not isinstance(gpos_dict, dict):
                    continue
                
                higher_ptv_int = max(
                    higher_ptv_int, gpos_dict['port_types_view'])

            for gpos_dict in group_positions:
                if not isinstance(gpos_dict, dict):
                    continue
                
                if gpos_dict['port_types_view'] == higher_ptv_int:
                    gpos_dict['port_types_view'] = PortTypesViewFlag.ALL.value

                self.views.add_old_json_gpos(gpos_dict)
        
        self._prevent_next_editor_update = True
        self.main_win.ui.plainTextEditPorts.setPlainText(editor_text)
        self._prevent_next_editor_update = False
        self.update_from_text(self.main_win.get_editor_text())
        
        for port_out_name, port_in_name in connections:
            self.add_connection(port_out_name, port_in_name)

        self.sg.views_changed.emit()
        self.view_number = self.views.first_view_num()
        self.change_view(self.view_number)

        return True

