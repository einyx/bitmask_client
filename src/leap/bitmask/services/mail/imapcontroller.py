# -*- coding: utf-8 -*-
# imapcontroller.py
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
IMAP service controller.
"""
import logging

from leap.bitmask.services.mail import imap


logger = logging.getLogger(__name__)


class IMAPController(object):
    """
    IMAP Controller.
    """
    def __init__(self, soledad, keymanager):
        """
        Initialize IMAP variables.

        :param soledad: a transparent proxy that eventually will point to a
                        Soledad Instance.
        :type soledad: zope.proxy.ProxyBase
        :param keymanager: a transparent proxy that eventually will point to a
                           Keymanager Instance.
        :type keymanager: zope.proxy.ProxyBase
        """
        self._soledad = soledad
        self._keymanager = keymanager

        self.incoming_mail = None  # XXX: this should live in it's own controller
        self.imap_port = None
        self.imap_factory = None

    def start_imap_service(self, userid, offline=False):
        """
        Start IMAP service.

        :param userid: user id, in the form "user@provider"
        :type userid: str
        :param offline: whether imap should start in offline mode or not.
        :type offline: bool
        """
        logger.debug('Starting imap service')

        self.imap_port, self.imap_factory = imap.start_imap_service(
            self._soledad,
            userid=userid)

        def assign_incoming_mail(incoming_mail):
            self.incoming_mail = incoming_mail

        if offline is False:
            logger.debug("Starting loop")
            d = imap.start_incoming_mail_service(
                self._keymanager,
                self._soledad,
                self.imap_factory,
                userid)
            d.addCallback(assign_incoming_mail)

    def stop_imap_service(self, cv):
        """
        Stop IMAP service (fetcher, factory and port).

        :param cv: A condition variable to which we can signal when imap
                   indeed stops.
        :type cv: threading.Condition
        """
        if self.incoming_mail_service is not None:
            # Stop the loop call in the fetcher
            self.incoming_mail_service.stopService()
            self.incoming_mail_service = None

        if self.imap_port is not None:
            # Stop listening on the IMAP port
            self.imap_port.stopListening()

            # Stop the protocol
            self.imap_factory.theAccount.closed = True
            self.imap_factory.doStop(cv)
        else:
            # Release the condition variable so the caller doesn't have to wait
            cv.acquire()
            cv.notify()
            cv.release()

    def fetch_incoming_mail(self):
        """
        Fetch incoming mail.
        """
        if self.incoming_mail_service is not None:
            logger.debug('Client connected, fetching mail...')
            self.incoming_mail_service.fetch()
