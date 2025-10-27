#!/usr/bin/make -f
# Makefile for Patchichi #
# ---------------------- #
# Created by houston4444
#
PREFIX ?= /usr/local
DESTDIR =
DEST_PATCHICHI := $(DESTDIR)$(PREFIX)/share/patchichi

LINK = ln -s -f
LRELEASE ?= lrelease
RCC ?= rcc
QT_VERSION ?= 6

# if you set QT_VERSION environment variable to 5 at the make command
# it will choose the other commands QT_API, pyuic5, pylupdate5.
# You will can run patchichi directly in source without install

ifeq ($(QT_VERSION), 6)
	QT_API ?= PyQt6
	PYUIC ?= pyuic6
	PYLUPDATE ?= pylupdate6
	RCC_EXEC := $(shell which $(RCC))
	RCC_QT6_DEB := /usr/lib/qt6/libexec/rcc

	ifeq (, ${RCC_EXEC})
		RCC := ${RCC_QT6_DEB}
	else
		ifeq ($(shell readlink ${RCC_EXEC}), qtchooser)
			ifeq ($(shell test -x ${RCC_QT6_DEB} | echo $$?), 0)
				RCC := ${RCC_QT6_DEB}
			endif
		endif
	endif

	ifeq (, $(shell which $(LRELEASE)))
		LRELEASE := lrelease-qt6
	endif
else
    QT_API ?= PyQt5
	PYUIC ?= pyuic5
	PYLUPDATE ?= pylupdate5
	ifeq (, $(shell which $(LRELEASE)))
		LRELEASE := lrelease-qt5
	endif
endif

# neeeded for make install
BUILD_CFG_FILE := src/qt_api.py
QT_API_INST := $(shell grep ^QT_API= $(BUILD_CFG_FILE) 2>/dev/null| cut -d'=' -f2| cut -d"'" -f2)
QT_API_INST ?= PyQt5

ICON_SIZES := 16 24 32 48 64 96 128 256

PYTHON := python3
ifeq (, $(shell which $(PYTHON)))
  PYTHON := python
endif

PATCHBAY_DIR=HoustonPatchbay

# ---------------------

all: PATCHBAY QT_PREPARE UI RES LOCALE

PATCHBAY:
	@(cd $(PATCHBAY_DIR) && $(MAKE))

QT_PREPARE:
	$(info compiling for Qt$(QT_VERSION) using $(QT_API))
	$(file > $(BUILD_CFG_FILE),QT_API='$(QT_API)')

    ifeq ($(QT_API), $(QT_API_INST))
    else
		rm -f *~ src/*~ src/*.pyc src/ui/*.py \
		    resources/locale/*.qm src/resources_rc.py
    endif
	install -d src/ui

# ---------------------
# Resources

RES: src/resources_rc.py

src/resources_rc.py: resources/resources.qrc
	rcc -g python $< |sed 's/ PySide. / qtpy /' > $@

# ---------------------
# UI code

UI: $(shell \
	ls resources/ui/*.ui| sed 's|\.ui$$|.py|'| sed 's|^resources/|src/|')

src/ui/%.py: resources/ui/%.ui
	$(PYUIC) $< -o $@
	
# ------------------------
# # Translations Files

LOCALE: locale

locale: locale/patchichi_en.qm \
		locale/patchichi_fr.qm \

locale/%.qm: locale/%.ts
	$(LRELEASE) $< -qm $@

# -------------------------

clean:
	@(cd $(PATCHBAY_DIR) && $(MAKE) $@)
	rm -f *~ src/*~ src/*.pyc  locale/*.qm src/resources_rc.py
	rm -f -R src/ui
	rm -f -R src/__pycache__ src/*/__pycache__ src/*/*/__pycache__ \
		  src/*/*/*/__pycache__
	rm -f src/qt_api.py

# -------------------------

debug:
	$(MAKE) DEBUG=true

# -------------------------

install:
# 	# Create directories
	install -d $(DESTDIR)$(PREFIX)/bin/
	install -d $(DESTDIR)$(PREFIX)/share/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/
	install -d $(DESTDIR)$(PREFIX)/share/applications/
	install -d $(DEST_PATCHICHI)/
	install -d $(DEST_PATCHICHI)/locale/
	install -d $(DEST_PATCHICHI)/$(PATCHBAY_DIR)/
	install -d $(DEST_PATCHICHI)/$(PATCHBAY_DIR)/locale
	
# 	# Copy Desktop Files
	install -m 644 data/share/applications/*.desktop \
		$(DESTDIR)$(PREFIX)/share/applications/

# 	# Install icons
	# Install icons
	for sz in $(ICON_SIZES);do \
		install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/$${sz}x$${sz}/apps/ ;\
		install -m 644 resources/main_icon/$${sz}x$${sz}/patchichi.png \
			$(DESTDIR)$(PREFIX)/share/icons/hicolor/$${sz}x$${sz}/apps/ ;\
	done

# 	# Install icons, scalable
	install -m 644 resources/main_icon/scalable/patchichi.svg \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/

#	# Copy patchbay themes
	cp -r HoustonPatchbay/themes $(DEST_PATCHICHI)/$(PATCHBAY_DIR)/
	cp -r HoustonPatchbay/manual $(DEST_PATCHICHI)/$(PATCHBAY_DIR)/
	cp -r HoustonPatchbay/patchbay $(DEST_PATCHICHI)/$(PATCHBAY_DIR)/

# 	# Install main code
	cp -r src $(DEST_PATCHICHI)/
	
# 	# compile python files
	$(PYTHON) -m compileall $(DEST_PATCHICHI)/src/
	$(PYTHON) -m compileall $(DEST_PATCHICHI)/patchbay/
	
# 	# install local manual
# 	cp -r manual $(DEST_PATCHICHI)/
		
#   # install launcher to bin
	install -m 755 data/bin/patchichi  $(DESTDIR)$(PREFIX)/bin/

# 	# Install Translations
	install -m 644 locale/*.qm $(DEST_PATCHICHI)/locale/
	install -m 644 $(PATCHBAY_DIR)/locale/*.qm $(DEST_PATCHICHI)/$(PATCHBAY_DIR)/locale/

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/patchichi
	rm -f $(DESTDIR)$(PREFIX)/share/applications/patchichi.desktop
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/*/apps/patchichi.png
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/patchichi.svg
	rm -rf $(DEST_PATCHICHI)
