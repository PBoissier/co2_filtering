# -*- coding: utf-8 -*-
'''
Created on 29 may 2017

:copyright:
    Observatoire Volcanologique du Piton de La Fournaise
    Institut de Physique du Globe de Paris
    Patrice Boissier (boissier@ipgp.fr)
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
'''
import datetime
from co2_filtering.data.DataAccessor import DataAccessor
from co2_filtering.configuration.Configuration import Configuration
import csv


if __name__ == '__main__':

    # Loading configuration
    conf_start = Configuration("./resources")
    # conf_start.show_configuration()

    # DataAccessor instanciation
    data_accessor = DataAccessor(conf_start.get_host(),
                                 conf_start.get_user(),
                                 conf_start.get_password(),
                                 conf_start.get_database())

    # Filter and outputs data for each station of the network
    for station in conf_start.get_network().get_stations():
        print("######\n%s\n######\n" % (station.get_name()))

        # Get data from the database
        table = conf_start.get_table_name(station.get_name())
        begin_date = conf_start.get_start_name(station.get_name())
        end_date = datetime.datetime.now()
        data = data_accessor.get_data(str(begin_date),
                                      str(end_date),
                                      conf_start.
                                      get_attributes_station(station.
                                                             get_name()),
                                      table)

        print("Initial data size : %s" % (data.__len__()))

        # Apply filters
        filtered_data = station.get_data_filter().\
            apply_filters(data, conf_start.get_processes_station(station.
                                                                 get_name()))

        # TODO : write class for CSV file writing
        # Awfully Quick'n'dirty!!!
        csv_cols = conf_start.get_output_headers(station.get_name()).__len__()
        file_name = "%s.csv" % (station.get_name())
        with open(file_name, 'wb') as out:
            csv_out = csv.writer(out, delimiter=';')
            csv_out.writerow(conf_start.get_output_headers(station.get_name()))
            for line in filtered_data:
                write_line = []
                write_line.append(line[0])
                if line.__len__() > 1:
                    for i in range(1, csv_cols):
                        write_line.append(line[i])
                csv_out.writerow(write_line)

        print("Filtered data size : %s" % (filtered_data.__len__()))
        print("\n")

    data_accessor.close()
