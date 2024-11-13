# ---  INSTALL for PATCHICHI  ---

Before installing, please uninstall any existing Patchichi installation: <br/>
`$ [sudo] make uninstall`

To install Patchichi, simply run as usual: <br/>
`$ make` <br/>
`$ [sudo] make install`

if you prefer to build it with Qt6, run instead: <br/>
`$ QT_VERSION=6 make` <br/>
`$ [sudo] make install`

depending of the distribution you'll need to use LRELEASE variable to install.
If you don't have 'lrelease' executable but 'lrelease-qt5' use:
`$ make LRELEASE=lrelease-qt5` <br/>
`$ [sudo] make install`

You can run Patchichi without install, by using instead: <br/>
`$ make` <br/>
`$ ./src/patchichi.py`

Packagers can make use of the 'PREFIX' and 'DESTDIR' variable during install, like this: <br/>
`$ make install PREFIX=/usr DESTDIR=./test-dir`

To uninstall Patchichi, run: <br/>
`$ [sudo] make uninstall`
<br/>

===== BUILD DEPENDENCIES =====
--------------------------------
The required build dependencies are: <i>(devel packages of these)</i>
 - python3-qtpy
 - PyQt5 or PyQt6
 - Qt5 or Qt6 dev tools 
 - qtchooser

On Debian and Ubuntu, use these commands to install all build dependencies: <br/>

to build it with Qt5:
`$ sudo apt-get install python3-qtpy python3-pyqt5 pyqt5-dev-tools qtchooser qttools5-dev-tools`

to build it with Qt6:
`$ sudo apt-get install python3-qtpy python3-pyqt6 pyqt6-dev-tools qtchooser`

===== RUNTIME DEPENDENCIES =====
--------------------------------

If the python3-pyqt-qtwebengine is present, the editor help will be displayed in a dialog window, else it will start a web browser.
