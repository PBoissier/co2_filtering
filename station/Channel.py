# -*- coding: utf-8 -*-
"""
Created on 30 juil. 2013

:copyright:
    Observatoire Volcanologique du Piton de La Fournaise
    Institut de Physique du Globe de Paris
    Patrice Boissier (boissier@ipgp.fr)
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""


class Channel(object):
    """
    Class representing a station component
    """

    def __init__(self, channel_name, channel_name_out, channel_order,
                 channel_process):
        """
        Constructor

        :type channel_name: String.
        :param channel_name: the channel name.
        :type channel_name_out: String.
        :param channel_name_out: the output channel name.
        :type channel_order: Integer.
        :param channel_order: the channel order.
        :type channel_process: String.
        :param channel_process: the channel processing scheme.
        """
        self._name = str(channel_name)
        if channel_name_out is None:
            self._name_out = None
        else:
            self._name_out = str(channel_name_out)
        if channel_order is None:
            self._order = None
        else:
            self._order = int(channel_order)
        if channel_process is None:
            self._process = None
        else:
            self._process = str(channel_process)

    def __str__(self):
        """
        String representation of the object

        :rtype: String.
        :return: the channel name.
        """
        return "%s - %s - %s - %s" % (self._name, self._name_out,
                                      self._order, self._process)

    def set_name(self, channel_name):
        """
        Sets the channel name

        :type channel_name: String.
        :param channel_name: the channel name.
        """
        self._name = str(channel_name)

    def get_name(self):
        """
        Returns the channel name

        :rtype: String.
        :return: the channel name.
        """
        return self._name

    def set_name_out(self, channel_name_out):
        """
        Sets the channel output name

        :type channel_name_out: String.
        :param channel_name_out: the channel name.
        """
        self._name_out = str(channel_name_out)

    def get_name_out(self):
        """
        Returns the component output name

        :rtype: String.
        :return: the channel output name.
        """
        return self._name_out

    def set_order(self, channel_order):
        """
        Sets the channel order

        :type channel_order: Integer.
        :param channel_order: the channel order.
        """
        self._order = str(channel_order)

    def get_order(self):
        """
        Returns the component order

        :rtype: Integer.
        :return: the channel order.
        """
        return self._order

    def set_process(self, channel_process):
        """
        Sets the channel process

        :type channel_process: String.
        :param channel_process: the channel process.
        """
        self._name = str(channel_process)

    def get_process(self):
        """
        Returns the channel process

        :rtype: String.
        :return: the channel process.
        """
        return self._name
