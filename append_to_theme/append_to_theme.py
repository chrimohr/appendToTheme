# -*- coding: utf-8 -*-
"""
/***************************************************************************
 appendToTheme
                                 A QGIS plugin
 Append Layer to all selected map themes
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-05-20
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Christoph Mohr
        email                : moin@chrimohr.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import *
from qgis.utils import iface

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .append_to_theme_dialog import appendToThemeDialog
import os.path


class appendToTheme:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'appendToTheme_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&appendToTheme')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('appendToTheme', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/append_to_theme/addIcon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Append To Theme'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&appendToTheme'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        if self.first_start == True:
            self.first_start = False
            self.dlg = appendToThemeDialog()

            # Project Variables
            root = QgsProject.instance().layerTreeRoot()
            mapThemesCollection = QgsProject.instance().mapThemeCollection()
            mapThemes = mapThemesCollection.mapThemes()

            # Clear comboBox
            self.dlg.groupComboBox.clear()
            self.dlg.themeComboBox.clear()

            # Populate the comboBox
            layerGroups = self.getGroups(root)
            self.dlg.groupComboBox.addItems([layerGroups.name() for layerGroups in layerGroups])
            self.dlg.themeComboBox.addItems([mapThemes for mapThemes in mapThemes])

            # Preselect all Themes
            self.dlg.themeComboBox.selectAllOptions()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Get selected
            selectedGroups = self.dlg.groupComboBox.checkedItems()
            selectedThemes = self.dlg.themeComboBox.checkedItems()

            selectedLayer = self.dlg.mMapLayerComboBox.currentLayer()

            # Get Layers that will be added
            layersToAdd = self.getLayersInSelectedGroups(root, selectedGroups)

            if selectedLayer:
                layersToAdd.append(selectedLayer.id())
                print(selectedLayer.id())

            # Recreate each selected map theme and add all selected Layers
            for theme in selectedThemes:
                layersToKeep = self.getLayersInTheme(mapThemesCollection, theme)
                newLayers = layersToAdd + layersToKeep
                self.recreateTheme(root, mapThemesCollection, theme, newLayers)

            self.iface.messageBar().pushMessage("Success", "Theme replaced", level=Qgis.Success, duration=3)
            pass

    def getGroups(self, root):
        groups = []
        for child in root.children():
            if isinstance(child, QgsLayerTreeGroup):
                groups.append(child)
        return groups

    def getLayersInTheme(self, mapThemesCollection, theme):
        layersInThemes = []
        themeVisibleLayers = mapThemesCollection.mapThemeVisibleLayers(theme)

        for layer in themeVisibleLayers:
            layersInThemes.append(layer.id())
        return layersInThemes

    def getLayersInGroup(self, group):
        layersInGroup = []
        for child in group.children():
            if isinstance(child, QgsLayerTreeGroup):
                self.getLayersInGroup(child)
            else:
                layersInGroup.append(child.layerId())
        return layersInGroup

    def getLayersInSelectedGroups(self, root, groups):
        layers = []
        for group in groups:
            realGroup = root.findGroup(group)
            layers.extend(self.getLayersInGroup(realGroup))
        return layers

    def changeLayerVisibility(self, group, newLayers):
        group.setItemVisibilityChecked(False)
        for child in group.children():
            if isinstance(child, QgsLayerTreeGroup):
                self.changeLayerVisibility(child, newLayers)  # unendlich?
            else:
                if (child.layerId() in newLayers):
                    child.setItemVisibilityChecked(True)
                    group.setItemVisibilityChecked(True)
                else:
                    child.setItemVisibilityChecked(False)

    def recreateTheme(self, root, mapThemesCollection, theme, newLayers):
        for child in root.children():
            if isinstance(child, QgsLayerTreeGroup):
                self.changeLayerVisibility(child, newLayers)
            elif isinstance(child, QgsLayerTreeLayer):
                if (child.layerId() in newLayers):
                    child.setItemVisibilityChecked(True)
                else:
                    child.setItemVisibilityChecked(False)
        mapThemeRecord = QgsMapThemeCollection.createThemeFromCurrentState(
            QgsProject.instance().layerTreeRoot(),
            self.iface.layerTreeView().layerTreeModel()
        )
        mapThemesCollection.update(theme, mapThemeRecord)
