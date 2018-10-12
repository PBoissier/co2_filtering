# -*- coding: utf-8 -*-
"""
Created on 31 juil. 2013


:copyright:
    Observatoire Volcanologique du Piton de La Fournaise
    Institut de Physique du Globe de Paris
    Patrice Boissier (boissier@ipgp.fr)
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
import os
import datetime
from lxml import etree
from co2_filtering.station.Channel import Channel
from co2_filtering.station.Station import Station
from co2_filtering.station.Network import Network
from co2_filtering.data.Filter import Filter


class Configuration(object):
    """
    Class representing the application configuration
    """

    def __init__(self, path):
        """
        Constructor
        """
        configuration_file_name = path + "/co2_filtering.xml"
        if os.path.exists(configuration_file_name):
            self.parse_configuration_file(configuration_file_name)
        else:
            raise IOError()

    def get_log_file(self):
        """
        Returns the log file name

        :rtype: String.
        :return: returns the log file name.
        """
        return self._log_file

    def get_threshold_filtered(self):
        """
        Returns the filtering threshold per day.

        :rtype: Integer.
        :return: returns the filtreing threshold.
        """
        return self._threshold_filtered

    def get_network(self):
        """
        Returns the network

        :rtype: Network.
        :return: returns the network
        """
        return self._network

    def get_table_name(self, station_name):
        """
        Returns a table name based on the station name

        :rtype: String.
        :return: returns the table name
        """
        return self._table_station[station_name]

    def get_start_name(self, station_name):
        """
        Returns a start date based on the station name

        :rtype: Datetime.
        :return: returns the station start date
        """
        return self._start_station[station_name]

    def get_headers(self, station_name):
        """
        Returns the headers based on the station name

        :rtype: List.
        :return: returns the headers
        """
        return self._headers_station[station_name]

    def get_output_headers(self, station_name):
        """
        Returns the output headers based on the station name

        :rtype: List.
        :return: returns the output headers
        """
        return self._output_headers_station[station_name]

    def get_attributes_station(self, station_name):
        """
        Returns the station table attributes based on the station name

        :rtype: String.
        :return: returns the station table attributes.
        """
        return self._attributes_station[station_name]

    def get_processes_station(self, station_name):
        """
        Returns the station processes based on the station name

        :rtype: List.
        :return: returns the list of this station processes.
        """
        return self._processes_station[station_name]

    def get_host(self):
        """
        Returns the hostname of the database.

        :rtype: String.
        :return: returns the hostname of the database.
        """
        return self._host

    def get_port(self):
        """
        Returns the database TCP port.

        :rtype: Integer.
        :return: returns the database TCP port.
        """
        return self._port

    def get_database(self):
        """
        Returns database name.

        :rtype: String.
        :return: returns database name.
        """
        return self._database

    def get_user(self):
        """
        Returns the database user name.

        :rtype: String.
        :return: returns the database user name.
        """
        return self._user

    def get_password(self):
        """
        Returns the database user password.

        :rtype: String.
        :return: returns the database user password.
        """
        return self._password

    def show_configuration(self):
        """
        Prints the application configuration in a readable way
        """
        print("Fichier de log : " + self._log_file)
        print("Le serveur de base de donnees : " + (self._host))
        print("Le port de la BD : " + str(self._port))
        print("Le nom de la BD : " + (self._database))
        print("L'utilisateur de la BD : " + (self._user))
        print("Le mot de passe de l'utilisateur de la BD : " +
              (self._password))
        print("Réseau : " + str(self._network))

    def update_web_conf(self):
        """
        Update configuration based on the Web configuration form
        """

    def parse_configuration_file(self, file_name):
        """
        Parse the XML configuration file

        :type file_name: String.
        :param file_name: the configuration file name
        """

        try:
            self._table_station = dict()
            self._start_station = dict()
            self._output_headers_station = dict()
            self._headers_station = dict()
            self._attributes_station = dict()
            self._processes_station = dict()
            tree = etree.parse(file_name)
            self._log_file = tree.findtext("program/log_file")
            self._threshold_filtered = int(tree.findtext("program/threshold_filtered"))
            network_name = tree.find("network").attrib['name']
            station_list = []
            station_attributes = tree.findall("network/station")
            for station_attribute in (station_attributes):
                output_headers = ["Date"]
                headers = ["Date"]
                attributes = ""
                processes = list()
                station_name = station_attribute.attrib['name']
                self._table_station[station_name] = station_attribute.\
                    attrib['table_name']
                self._start_station[station_name] = datetime.datetime.\
                    strptime(station_attribute.attrib['start'],
                             "%Y-%m-%d %H:%M:%S")
                channel_list = []
                channel_order = 1
                channel_attributes = station_attribute.findall("channel")
                for channel_attribute in (channel_attributes):
                    channel_name_in = channel_attribute.attrib['name_in']
                    attributes = attributes + ", " + channel_name_in
                    channel_name_out = channel_attribute.findtext("out_name")
                    channel_process = channel_attribute.findtext("process")
                    processes.append(channel_process)
                    if channel_name_out is None:
                        headers.append(channel_name_in)
                    else:
                        headers.append(channel_name_out)
                        output_headers.append(channel_name_out)
                    channel = Channel(channel_name_in, channel_name_out,
                                      channel_order, channel_process)
                    channel_list.append(channel)
                    channel_order += 1
                # FILTER
                data_filter = Filter(float(station_attribute.
                                     findtext("filters/air_pressure_filter/"
                                              "pressure_min")),
                                     float(station_attribute.
                                     findtext("filters/air_pressure_filter/"
                                              "pressure_max")),
                                     int(station_attribute.
                                     findtext("filters/air_pressure_filter/"
                                              "pressure_index")),
                                     float(station_attribute.
                                     findtext("filters/co2_0_filter/"
                                              "co2_0_min")),
                                     float(station_attribute.
                                     findtext("filters/co2_0_filter/"
                                              "co2_0_max")),
                                     int(station_attribute.
                                     findtext("filters/co2_0_filter/"
                                              "co2_0_index")),
                                     self._threshold_filtered)
                station = Station(station_name, channel_list, data_filter)
                self._output_headers_station[station_name] = output_headers
                self._headers_station[station_name] = headers
                self._attributes_station[station_name] = attributes
                self._processes_station[station_name] = processes
                station_list.append(station)
            self._network = Network(network_name, station_list)
            self._host = tree.findtext("dbms/host")
            self._port = int(tree.findtext("dbms/port"))
            self._database = tree.findtext("dbms/database")
            self._user = tree.findtext("dbms/user")
            self._password = tree.findtext("dbms/password")

        except Exception:
            print("Unexpected error during configuration")
