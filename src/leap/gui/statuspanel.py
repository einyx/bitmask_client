# -*- coding: utf-8 -*-
# statuspanel.py
# Copyright (C) 2013 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Status Panel widget implementation
"""
import logging

from functools import partial
from PySide import QtCore, QtGui

from ui_statuspanel import Ui_StatusPanel
from leap.common.check import leap_assert
from leap.services.eip.vpnprocess import VPNManager
from leap.platform_init import IS_WIN, IS_LINUX
from leap.common.check import leap_assert_type

logger = logging.getLogger(__name__)

#background: qlineargradient(
#x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #%(groove_background)s);

toggleStyleSheet = """
QSlider::groove:horizontal {
 border: 1px solid #999999;
 border-radius: 3px;
 height: 20px;
 /* the groove expands to the size of the slider by default.*/
 /* by giving it a   height, it has a fixed size */
 margin: 2px 0;
 background-image: url(:/images/eip-slider-%(status)s.png);
}

QSlider::handle:horizontal {
 border: 1px solid #5c5c5c;
 width: 45px;
 height: 20px;
 margin: -2px 0;
 /* handle is placed by default on the contents rect */
 /* of the groove. Expand outside the groove */
 border-radius: 3px;
 background: qlineargradient(
  x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
}
"""


class StatusPanelWidget(QtGui.QWidget):
    """
    Status widget that displays the current state of the LEAP services
    """
    EIPToggledOn = QtCore.Signal()
    EIPToggledOff = QtCore.Signal()

    start_eip = QtCore.Signal()
    stop_eip = QtCore.Signal()

    SLIDER_EIPTOGGLE_MAXVAL = 100
    eipswitch_val = 0

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self._systray = None
        self._action_eip_status = None

        self.ui = Ui_StatusPanel()
        self.ui.setupUi(self)

        self.init_ui_eiptoggle()
        self.hide_status_box()
        self.init_eip_icons()

    def init_ui_eiptoggle(self):
        """
        Initializes the EIP Toggle Slider Widget.
        """
        self.ui.sliderEIPToggle.valueChanged[int].connect(
            lambda val: self.changeEIPToggleOnClicked(val))
        self.ui.sliderEIPToggle.sliderReleased.connect(
            lambda: self.changeEIPToggleOnReleased())
        self.setEIPToggleCustomStyle(on=False)
        self.EIPToggledOn.connect(self.start_eip)
        self.ui.sliderEIPToggle.setEnabled(False)

    def init_eip_icons(self):
        """
        Initialize EIP status icons.
        """
        # Set the EIP status icons
        self.CONNECTING_ICON = None
        self.CONNECTED_ICON = None
        self.ERROR_ICON = None
        self.CONNECTING_ICON_TRAY = None
        self.CONNECTED_ICON_TRAY = None
        self.ERROR_ICON_TRAY = None
        self._set_eip_icons()

    # ON/OFF slider toggle functions

    def sliderEIPToggleChangeValue(self, value):
        """
        Changes value for the EIP Toggle Slider.
        :param value: new value
        :type value: int
        """
        slider = self.ui.sliderEIPToggle
        self.eipswitch_val = slider.value()
        slider.setValue(value)

        if value == self.SLIDER_EIPTOGGLE_MAXVAL:
            self.EIPToggledOn.emit()
        else:
            self.EIPToggledOff.emit()

    def sliderEIPToggleOn(self):
        """
        Sets slider to ON state, in progress background.
        """
        self.sliderEIPToggleChangeValue(self.SLIDER_EIPTOGGLE_MAXVAL)
        self.setEIPToggleCustomStyle(on=True, inprogress=True)

    def sliderEIPToggleConnected(self):
        """
        Sets slider to ON state, with the ON background.
        """
        self.sliderEIPToggleChangeValue(self.SLIDER_EIPTOGGLE_MAXVAL)
        self.setEIPToggleCustomStyle(on=True, inprogress=False)

    def sliderEIPToggleOff(self):
        """
        Sets slider to OFF state.
        """
        self.sliderEIPToggleChangeValue(0)
        self.setEIPToggleCustomStyle(on=False)

    def changeEIPToggleOnClicked(self, value):
        """
        If we get a click on the groove, set the slider handle to the
        new position according to where the click is relative to the middle
        point.
        """
        slider = self.ui.sliderEIPToggle
        if not slider.isSliderDown():
            newvalue = value
            if value > self.eipswitch_val:
                newvalue = self.SLIDER_EIPTOGGLE_MAXVAL
                on = True
            else:
                newvalue = 0
                on = False
            self.setEIPToggleCustomStyle(on=on, inprogress=True)
            self.sliderEIPToggleChangeValue(newvalue)

    def changeEIPToggleOnReleased(self):
        """
        When the slider is released, set the new value according to the
        position relative to the middle point.
        """
        slider = self.ui.sliderEIPToggle
        value = slider.sliderPosition()
        if value > (self.SLIDER_EIPTOGGLE_MAXVAL/2):
            newvalue = self.SLIDER_EIPTOGGLE_MAXVAL
            on = True
        else:
            newvalue = 0
            self.ui.sliderEIPToggle.setValue(0)
            on = False
        self.setEIPToggleCustomStyle(on=on, inprogress=True)
        self.sliderEIPToggleChangeValue(newvalue)

    def _get_toggle_style(self, status):
        """
        Gets the appropriate stylesheet for the current
        toggle status.
        :param status: slider status to style
        :type inprogress: string
        """
        leap_assert(status in ('on', 'off', 'inprogress'),
                    "invalid status for slider styles")
        return toggleStyleSheet % {"status": status}

    def setEIPToggleCustomStyle(self, on=True, inprogress=False):
        """
        Sets a custom stylesheet for the toggle slider.
        :param on: whether the widget is in on state.
        :type on: bool
        """
        set_style = self.ui.sliderEIPToggle.setStyleSheet
        if inprogress:
            status = "inprogress"
        else:
            status = "on" if on else "off"
        style = self._get_toggle_style(status)
        set_style(style)

    def set_startstop_enabled(self, value):
        """
        Enable or disable sliderEIPToggle based on value.

        :param value: True for enabled, False otherwise
        :type value: bool
        """
        leap_assert_type(value, bool)
        self.ui.sliderEIPToggle.setEnabled(value)

    def _set_eip_icons(self):
        """
        Sets the EIP status icons for the main window and for the tray

        MAC   : dark icons
        LINUX : dark icons in window, light icons in tray
        WIN   : light icons
        """
        EIP_ICONS = EIP_ICONS_TRAY = (
            ":/images/conn_connecting-light.png",
            ":/images/conn_connected-light.png",
            ":/images/conn_error-light.png")

        if IS_LINUX:
            EIP_ICONS_TRAY = (
                ":/images/conn_connecting.png",
                ":/images/conn_connected.png",
                ":/images/conn_error.png")
        elif IS_WIN:
            EIP_ICONS = EIP_ICONS_TRAY = (
                ":/images/conn_connecting.png",
                ":/images/conn_connected.png",
                ":/images/conn_error.png")

        self.CONNECTING_ICON = QtGui.QPixmap(EIP_ICONS[0])
        self.CONNECTED_ICON = QtGui.QPixmap(EIP_ICONS[1])
        self.ERROR_ICON = QtGui.QPixmap(EIP_ICONS[2])

        self.CONNECTING_ICON_TRAY = QtGui.QPixmap(EIP_ICONS_TRAY[0])
        self.CONNECTED_ICON_TRAY = QtGui.QPixmap(EIP_ICONS_TRAY[1])
        self.ERROR_ICON_TRAY = QtGui.QPixmap(EIP_ICONS_TRAY[2])

    def set_systray(self, systray):
        """
        Sets the systray object to use.

        :param systray: Systray object
        :type systray: QtGui.QSystemTrayIcon
        """
        leap_assert_type(systray, QtGui.QSystemTrayIcon)
        self._systray = systray

    def set_action_eip_status(self, action_eip_status):
        """
        Sets the action_eip_status to use.

        :param action_eip_status: action_eip_status to be used
        :type action_eip_status: QtGui.QAction
        """
        leap_assert_type(action_eip_status, QtGui.QAction)
        self._action_eip_status = action_eip_status

    def set_global_status(self, status, error=False):
        """
        Sets the global status label.

        :param status: status message
        :type status: str or unicode
        :param error: if the status is an erroneous one, then set this
                      to True
        :type error: bool
        """
        leap_assert_type(error, bool)
        if error:
            status = "<font color='red'><b>%s</b></font>" % (status,)
        self.ui.lblGlobalStatus.setText(status)
        self.ui.globalStatusBox.show()

    def hide_status_box(self):
        """
        Hide global status box.
        """
        self.ui.globalStatusBox.hide()

    def set_eip_status(self, status, error=False):
        """
        Sets the status label at the VPN stage to status

        :param status: status message
        :type status: str or unicode
        :param error: if the status is an erroneous one, then set this
                      to True
        :type error: bool
        """
        leap_assert_type(error, bool)

        self._systray.setToolTip(status)
        if error:
            status = "<font color='red'>%s</font>" % (status,)
        self.ui.lblEIPStatus.setText(status)

    def eip_pre_up(self):
        """
        Triggered when the app activates eip.
        Hides the status box and disables the start/stop button.
        """
        self.hide_status_box()
        self.set_startstop_enabled(False)

    def eip_started(self):
        """
        Sets the state of the widget to how it should look after EIP
        has started, ie, slider ON.
        """
        try:
            self.EIPToggledOn.disconnect()
        except RuntimeError:
            pass
        self.EIPToggledOff.connect(self.stop_eip)
        self.sliderEIPToggleOn()

    def eip_stopped(self):
        """
        Sets the state of the widget to how it should look after EIP
        has stopped, ie, slider OFF.
        """
        try:
            self.EIPToggledOff.disconnect()
        except RuntimeError:
            pass
        self.EIPToggledOn.connect(self.start_eip)
        self.sliderEIPToggleOff()

    def set_icon(self, icon):
        """
        Sets the icon to display for EIP

        :param icon: icon to display
        :type icon: QPixmap
        """
        self.ui.lblVPNStatusIcon.setPixmap(icon)

    def update_vpn_status(self, data):
        """
        SLOT
        TRIGGER: VPN.status_changed

        Updates the download/upload labels based on the data provided
        by the VPN thread
        """
        upload = float(data[VPNManager.TUNTAP_WRITE_KEY] or "0")
        upload = upload / 1000.0
        upload_str = "%12.2f Kb" % (upload,)
        self.ui.lblUpload.setText(upload_str)
        download = float(data[VPNManager.TUNTAP_READ_KEY] or "0")
        download = download / 1000.0
        download_str = "%12.2f Kb" % (download,)
        self.ui.lblDownload.setText(download_str)

    def update_vpn_state(self, data):
        """
        SLOT
        TRIGGER: VPN.state_changed

        Updates the displayed VPN state based on the data provided by
        the VPN thread
        """
        status = data[VPNManager.STATUS_STEP_KEY]
        self.set_eip_status_icon(status)
        if status == "CONNECTED":
            self.set_eip_status(self.tr("ON"))
            # Only now we can properly enable the button.
            self.sliderEIPToggleConnected()
            self.set_startstop_enabled(True)
        elif status == "AUTH":
            self.set_eip_status(self.tr("Authenticating..."))
        elif status == "GET_CONFIG":
            self.set_eip_status(self.tr("Retrieving configuration..."))
        elif status == "WAIT":
            self.set_eip_status(self.tr("Waiting to start..."))
        elif status == "ASSIGN_IP":
            self.set_eip_status(self.tr("Assigning IP"))
        elif status == "ALREADYRUNNING":
            # Put the following calls in Qt's event queue, otherwise
            # the UI won't update properly
            QtCore.QTimer.singleShot(0, self.stop_eip)
            QtCore.QTimer.singleShot(0, partial(self.set_global_status,
                                                self.tr("Unable to start VPN, "
                                                        "it's already "
                                                        "running.")))
        else:
            self.set_eip_status(status)

    def set_eip_status_icon(self, status):
        """
        Given a status step from the VPN thread, set the icon properly

        :param status: status step
        :type status: str
        """
        selected_pixmap = self.ERROR_ICON
        selected_pixmap_tray = self.ERROR_ICON_TRAY
        tray_message = self.tr("Encryption is OFF")
        if status in ("WAIT", "AUTH", "GET_CONFIG",
                      "RECONNECTING", "ASSIGN_IP"):
            selected_pixmap = self.CONNECTING_ICON
            selected_pixmap_tray = self.CONNECTING_ICON_TRAY
            tray_message = self.tr("Turning ON")
        elif status in ("CONNECTED"):
            tray_message = self.tr("Encryption is ON")
            selected_pixmap = self.CONNECTED_ICON
            selected_pixmap_tray = self.CONNECTED_ICON_TRAY

        self.set_icon(selected_pixmap)
        self._systray.setIcon(QtGui.QIcon(selected_pixmap_tray))
        self._action_eip_status.setText(tray_message)

    def set_provider(self, provider):
        self.ui.lblProvider.setText(provider)
