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
from co2_filtering.station.Channel import Channel
from co2_filtering.data.Filter import Filter


class Station(object):
    """
    Class representing a station
    """

    def __init__(self, station_name, channels, data_filter):
        """
        Constructor

        :type station_name: String.
        :param station_name: the station name.
        :type channels: List.
        :param channels: a list of Channel objects
        :type data_filter: Filter.
        :param data_filter: the data filter.
        """
        if type(channels) is not list:
            raise TypeError("Expected type is List")
        for channel in (channels):
            if type(channel) is not Channel:
                raise TypeError("Expected type is  Channel")
        if type(data_filter) is not Filter:
            raise TypeError("Expected type is Filter")
        self._name = str(station_name)
        self._channels = channels
        self._data_filter = data_filter

    def __str__(self):
        """
        String representation of the object

        :rtype: String.
        :return: the string representation of a station
        """
        output_string = self._name + "\n"
        for channel in (self._channels):
            output_string = output_string + "   - " + str(channel) + "\n"
        return output_string

    def set_name(self, station_name):
        """
        Sets the station name

        :type station_name: String.
        :param station_name: the station name.
        """
        self._name = str(station_name)

    def get_name(self):
        """
        Returns the station name

        :rtype: String.
        :return: the station name
        """
        return self._name

    def add_channel(self, channel):
        """
        Adds a component to the station

        :type channel: Channel.
        :param channel: the channel to add to the station
        """
        self._channels.append(channel)

    def get_channels(self):
        """
        Returns the station channel as a list

        :rtype: List.
        :return: a list of Channel objects
        """
        return self._channels

    def get_data_filter(self):
        """
        Returns the station filter

        :rtype: Filter.
        :return: the station name
        """
        return self._data_filter
