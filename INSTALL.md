# Preparing the source tree

If you just cloned the git repository, make sure you also
cloned the submodules, which you can do using:

`$ git submodule update --init`

# Building

## Build dependencies

The required build dependencies are: (devel packages of these)

 - PyQt6 (or PyQt5)
 - Qt6 dev tools (or Qt5 dev tools)
 - qtchooser (only for translations)
 - qttools5-dev-tools (only for translations, works for Qt5 and Qt6)

The difficulty with Qt6 build (which is the default), is sometimes to get the following executables:
- rcc
- lrelease

By chance, the compilation should work even if theses 2 tools are supposed to work with Qt5.


On Debian and Ubuntu, use these commands as root to install all build
dependencies:

- for Qt6 build:

`$ [sudo] apt install pyqt6-dev-tools qt6-base-dev-tools qtchooser qttools5-dev-tools`

- for Qt5 build:

`$ [sudo] apt install pyqt5-dev-tools qtchooser qttools5-dev-tools`


To build Patchichi, simply run as usual:

`$ make`

if you prefer to build it with Qt5:

`$ QT_VERSION=5 make`

Depending of the distribution you might need to use the LRELEASE variable
to build.  If you don't have 'lrelease' executable but 'lrelease-qt5' use:

`$ make LRELEASE=lrelease-qt5`

on Debian, you probably need to set RCC this way:
`$ RCC=/usr/lib/qt6/libexec/rcc make`

# Installing

To install Patchichi, simply run as usual:

`$ [sudo] make install`

Packagers can make use of the 'PREFIX' and 'DESTDIR' variable during install,
like this:

`$ [sudo] make install PREFIX=/usr DESTDIR=./test-dir`

# Uninstalling

To uninstall Patchichi, run:

`$ [sudo] make uninstall`

# Runtime dependencies

To run it, you'll additionally need:
   - qt6-svg-plugins (or probably libqt5svg5 for Qt5)
   - python3-pyqt6 (or python3-pyqt5 for Qt5)
   - python3-pyqt6.qtsvg (or python3-pyqt5 for Qt5)
   - python3-qtpy
   - Roboto font family (used by default patchbay theme)

Optional:
   - python3-pyqt6-qtwebengine (or python3-pyqt5-qtwebengine)

To install runtime dependencies on debian based systems, run:

`[sudo] apt install qt6-svg-plugins python3-pyqt6 python3-pyqt6.qtsvg python3-pyqt6-qtwebengine python3-qtpy fonts-roboto`

If the python3-pyqt-qtwebengine is present, the editor help will be displayed in a dialog window, else it will start a web browser.

# Running

You can run Patchichi without install, by using:

`$ ./src/patchichi.py`


