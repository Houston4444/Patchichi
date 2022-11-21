#!/usr/bin/make -f
# Makefile for Patchichi #
# ---------------------- #
# Created by houston4444
#
PREFIX ?= /usr/local
DESTDIR =
DEST_PATCHICHI := $(DESTDIR)$(PREFIX)/share/patchichi

LINK = ln -s -f
PYUIC := pyuic5
PYRCC := pyrcc5

LRELEASE := lrelease
ifeq (, $(shell which $(LRELEASE)))
 LRELEASE := lrelease-qt5
endif

ifeq (, $(shell which $(LRELEASE)))
 LRELEASE := lrelease-qt4
endif

PYTHON := python3
ifeq (, $(shell which $(PYTHON)))
  PYTHON := python
endif

PATCHBAY_DIR=HoustonPatchbay

# ---------------------

all: PATCHBAY UI RES LOCALE

PATCHBAY:
	@(cd $(PATCHBAY_DIR) && $(MAKE))

# ---------------------
# Resources

RES: src/resources_rc.py

src/resources_rc.py: resources/resources.qrc
	$(PYRCC) $< -o $@

# ---------------------
# UI code

UI: mkdir_ui patchichi 

mkdir_ui:
	@if ! [ -e src/ui ];then mkdir -p src/ui; fi

patchichi: src/ui/main_win.py \
		   src/ui/about_patchichi.py

src/ui/%.py: resources/ui/%.ui
	$(PYUIC) $< -o $@
	
PY_CACHE:
	$(PYTHON) -m compileall src/
	
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

# -------------------------

debug:
	$(MAKE) DEBUG=true

# -------------------------

install:
# 	# Create directories
	install -d $(DESTDIR)$(PREFIX)/bin/
	install -d $(DESTDIR)$(PREFIX)/share/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/24x24/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/32x32/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/64x64/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/96x96/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/
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
	install -m 644 resources/main_icon/16x16/patchichi.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
	install -m 644 resources/main_icon/24x24/patchichi.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/24x24/apps/
	install -m 644 resources/main_icon/32x32/patchichi.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/32x32/apps/
	install -m 644 resources/main_icon/48x48/patchichi.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
	install -m 644 resources/main_icon/64x64/patchichi.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/64x64/apps/
	install -m 644 resources/main_icon/96x96/patchichi.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/96x96/apps/
	install -m 644 resources/main_icon/128x128/patchichi.png \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
	install -m 644 resources/main_icon/256x256/patchichi.png \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/

# 	# Install icons, scalable
	install -m 644 resources/main_icon/scalable/patchichi.svg \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/

	# Copy patchbay themes
	cp -r HoustonPatchbay/themes $(DEST_PATCHICHI)/$(PATCHBAY_DIR)/

# 	# Install main code
	cp -r src $(DEST_PATCHICHI)/
	rm $(DEST_PATCHICHI)/src/patchbay
	cp -r $(PATCHBAY_DIR)/patchbay $(DEST_PATCHICHI)/src/
	
# 	# compile python files
	$(PYTHON) -m compileall $(DEST_PATCHICHI)/src/
	
# 	# install local manual
# 	cp -r manual $(DEST_PATCHICHI)/
		
#   # install main bash scripts to bin
	install -m 755 data/patchichi  $(DESTDIR)$(PREFIX)/bin/
	sed -i "s?X-PREFIX-X?$(PREFIX)?" $(DESTDIR)$(PREFIX)/bin/patchichi

# 	# Install Translations
	install -m 644 locale/*.qm $(DEST_PATCHICHI)/locale/
	install -m 644 $(PATCHBAY_DIR)/locale/*.qm $(DEST_PATCHICHI)/$(PATCHBAY_DIR)/locale/

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/patchichi
	rm -f $(DESTDIR)$(PREFIX)/share/applications/patchichi.desktop
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/*/apps/patchichi.png
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/patchichi.svg
	rm -rf $(DEST_PATCHICHI)
