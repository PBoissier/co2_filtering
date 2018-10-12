'''
Created on 13 juin 2017

:copyright:
    Observatoire Volcanologique du Piton de La Fournaise
    Institut de Physique du Globe de Paris
    Patrice Boissier (boissier@ipgp.fr)
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
'''
import numpy as np
import pandas as pd
import datetime
from datetime import timedelta


class Filter(object):
    '''
    Class representing a filter
    '''

    def __init__(self,
                 pressure_min, pressure_max, pressure_index,
                 co2_0_min, co2_0_max, co2_0_index, threshold_filtered):
        """
        Constructor

        :type pressure_min: Float.
        :param pressure_min: the minimum pressure allowed.
        :type pressure_max: Float.
        :param pressure_max: the maximum pressure allowed.
        :type pressure_index: Integer.
        :param pressure_index: the pressure field index.
        :type co2_0_min: Flaot.
        :param co2_0_min: the minimum CO2_0 value allowed.
        :type co2_0_max: Float.
        :param co2_0_max: the maximum CO2_0 value allowed.
        :type co2_0_index: Integer.
        :param co2_0_index: the CO2_0 field index.
        """
        self._pressure_min = pressure_min
        self._pressure_max = pressure_max
        self._pressure_index = pressure_index
        self._co2_0_min = co2_0_min
        self._co2_0_max = co2_0_max
        self._co2_0_index = co2_0_index
        self._threshold_filtered = threshold_filtered

    def show_parameters(self):
        """
        Shows filters parameters
        """
        print("-Air pressure filter : \npressure_min : %s\npressure_max : %s" %
              (self._pressure_min, self._pressure_max))
        print("-CO2_0 filter : \nco2_0_min : %s\nco2_0_max : %s" %
              (self._co2_0_min, self._co2_0_max))

    def air_pressure_filter(self, air_pressure_value):
        """
        Filter data using air pressure

        :type air_pressure_value: float.
        :param air_pressure_value: the air pressure value.
        :rtype: Bool.
        :return: True if the value needs to be filtered, False otherwize
        """
        to_be_filtered = True
        if air_pressure_value is not None:
            if air_pressure_value < self._pressure_max \
                    and air_pressure_value > self._pressure_min:
                to_be_filtered = False
        return to_be_filtered

    def co2_0_filter(self, co2_0_value):
        """
        Filter data using CO2_0

        :type co2_0_value: float.
        :param co2_0_value: the co2_0 value.
        :rtype: Bool.
        :return: True if the value needs to be filtered, False otherwize
        """
        to_be_filtered = True
        if co2_0_value is not None:
            if co2_0_value < self._co2_0_max and \
                    co2_0_value > self._co2_0_min:
                to_be_filtered = False
        return to_be_filtered

    def day_process(self, data, days_to_remove, processes):
        """
        Day process on hourly data.
        Accepted processing : mean and sum

        :type data: List.
        :param data: the hourly data.
        :type processes: List.
        :param processes: the processes to be applied daily.
        :rtype: List.
        :return: the day average data
        """
        # https://stackoverflow.com/questions/28304881/get-the-average-year-mean-of-days-over-multiple-years-in-pandas
        # TODO : refaire toute cette methode horriblement "Quick'n'dirty"!!!!
        output_data = []
        dates = []
        data_extract = []
        is_first_date = True
        first_date = None
        now_date = datetime.datetime.now()
        for row in data:
            if is_first_date:
                first_date = row[0].replace(hour=00, minute=00, second=00)
                is_first_date = False
            dates.append(row[0])
            data_extract.append(row[1:])

        data_extract = np.asarray(data_extract)

        output_ts = []
        output_dates = []

        for i in range(0, data_extract.shape[1]):
            ts = pd.Series(data_extract[:, i], dates)
            ts.fillna(value=np.nan, inplace=True)
            if processes[i] == "mean":
                output_ts.append(ts.groupby([ts.index.year,
                                             ts.index.month,
                                             ts.index.day]).mean().tolist())
                output_dates = ts.groupby([ts.index.year,
                                           ts.index.month,
                                           ts.index.day]).mean().index.values
            elif processes[i] == "sum":
                output_ts.append(ts.groupby([ts.index.year,
                                             ts.index.month,
                                             ts.index.day]).sum().tolist())
                output_dates = ts.groupby([ts.index.year,
                                           ts.index.month,
                                           ts.index.day]).sum().index.values

        # print(output_dates)
        # print("First date : %s" % first_date)
        output_dates_datetime = []
        for output_date_row in output_dates:
            temp_date = []
            for date_component in output_date_row:
                temp_date.append(int(date_component))
            output_dates_datetime.append(datetime.datetime(*temp_date))

        output_counter = 0
        while first_date <= now_date:
            output_data_line = []
            output_data_line.append(first_date.strftime("%d/%m/%y"))
            if first_date == output_dates_datetime[output_counter]:
                # Cas ou on a bien une mesure
                if not output_dates_datetime[output_counter] in days_to_remove:
                    # Cas ou cette mesure est OK
                    for j in range(0, output_ts.__len__()):
                        output_data_line.append(output_ts[j][output_counter])
                else:
                    print("Jour a supprimer %s" % output_dates_datetime[i])
                    for j in range(0, output_ts.__len__()):
                        output_data_line.append(None)
                output_counter += 1
            else:
                for j in range(0, output_ts.__len__()):
                    output_data_line.append(None)
            output_data.append(output_data_line)
            first_date += timedelta(days=1)

        return output_data

    def apply_filters(self, data, processes):
        """
        Apply all configured filters

        :type data: List.
        :param data: the data to be filtered.
        :type processes: List.
        :param processes: the processes to be applied daily.
        :rtype: List.
        :return: the filtered data
        """
        days_to_remove = []
        counter = 0
        output = []
        previous_date = None
        day_counter = 0
        first_filter = True
        for line in data:
            filter_pressure = self.air_pressure_filter(line[self._pressure_index])
            filter_co2_0 = self.co2_0_filter(line[self._co2_0_index])
            if not filter_pressure and not filter_co2_0:
                output.append(line)
            else:
                if first_filter:
                    previous_date = line[0].date()
                    first_filter = False
                if previous_date != line[0].date():
                    if line[0].date().strftime("%d/%m/%y") not in days_to_remove and day_counter >= self._threshold_filtered:
                        print ("Date a supprimer : %s - %s filtrages" % (line[0].date(), day_counter))
                        days_to_remove.append(line[0].date().strftime("%d/%m/%y"))
                    previous_date = line[0].date()
                    day_counter = 0
                day_counter += 1
                empty_line = list()
                for i in range(0, line.__len__()):
                    if i == 0:
                        empty_line.append(line[i])
                    else:
                        empty_line.append(None)
                output.append(empty_line)
                counter += 1

        data = self.day_process(output, days_to_remove, processes)

        return data


