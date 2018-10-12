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


class Network(object):
    """
    Class representing a network
    """

    def __init__(self, network_name, stations=[]):
        """
        Constructor

        :type network_name: String.
        :param network_name: the network name
        :type stations: List.
        :param stations: list of Station objects
        """
        if type(stations) is not list:
            raise TypeError("Le type attendu est une liste")

        self._name = str(network_name)
        self._stations = stations

    def __str__(self):
        """
        String representation of the object

        :rtype: String.
        :return: the string representation of the network
        """
        output_string = self._name + "\n"
        for station in (self._stations):
            output_string = output_string + " - " + str(station) + "\n"
        return output_string

    def set_name(self, network_name):
        """
        Sets the network name

        :type network_name: String.
        :param network_name: the network name
        """
        self._name = str(network_name)

    def get_name(self):
        """
        Returns the network name

        :rtype: String.
        :return: the network name
        """
        return self._name

    def add_station(self, station):
        """
        Adds a seismic station to the network

        :type stations: Station.
        :param stations: the station to add to the network.
        """
        self._stations.append(station)

    def get_stations(self):
        """
        Returns the network stations as a list

        :rtype: List.
        :return: a list of Station objects
        """
        return self._stations
