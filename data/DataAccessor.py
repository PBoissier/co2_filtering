# -*- coding: utf-8 -*-
'''
Created on 3 oct. 2013

:copyright:
    Observatoire Volcanologique du Piton de La Fournaise
    Institut de Physique du Globe de Paris
    Patrice Boissier (boissier@ipgp.fr)
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
'''
import MySQLdb
from collections import OrderedDict


class DataAccessor(object):
    '''
    Class representing a data accessor
    '''

    def __init__(self, db_host, db_user, db_password, db_database):
        '''
        Constructor

        :type db_host: String.
        :param db_host: the database IP or hostname
        :type db_user: String.
        :param db_user: the database user
        :type db_password: String.
        :param db_password: the database password
        :type db_database: String.
        :param db_database: the database
        '''
        self.db = MySQLdb.connect(db_host, db_user, db_password, db_database)
        self.cursor = self.db.cursor()

    def close(self):
        '''
        Closes the connection
        '''
        self.cursor.close()

    def get_data(self, begin, end, parameters, table):
        '''
        Returns a date/value serie based on a time period, parameter and table

        :type begin: Datetime.
        :param begin: the begin date
        :type end: Datetime.
        :param end: the end date
        :type parameters: List.
        :param parameters: the parameters list
        :type table: String.
        :param table: the database table
        :rtype: List.
        :return: the data list normalized
        :rtype: List.
        :return: the data list normalized
        '''
        statement = ('SELECT Date ' + parameters + ' FROM ' + table +
                     ' WHERE Date > \'' + begin + '\' AND Date < \'' +
                     end + '\';')
        values = []
        try:
            self.cursor.execute(statement)
            for row in self.cursor:
                value_list = []
                date_value = True
                for value in row:
                    if date_value:
                        value_list.append(value)
                    else:
                        value_list.append(float(value))
                    date_value = False
                values.append(value_list)
        except Exception as error:
            print 'Error reading from database:', error
        return values

    def create_table(self, table_name, attributes):
        '''
        Create table

        :type table_name: String.
        :param table_name: the table name
        :type attributes: Dict.
        :param attributes: the attributes of the table
        '''
        statement = 'DROP TABLE IF EXISTS ' + table_name + ';'
        self.cursor.execute(statement)
        statement = 'CREATE TABLE ' + table_name + ' ('
        counter = 0
        for key, value in attributes.items():
            if counter < len(attributes.keys()) - 1:
                statement += '%s %s, ' % (key, value)
            else:
                statement += '%s %s);' % (key, value)
            counter += 1
        self.cursor.execute(statement)

    def insert_data(self, table_name, attributes, data):
        '''
        Insert data in the table

        :type table_name: String.
        :param table_name: the table name
        :type data: List.
        :param data: the data to insert
        '''
        statement_prefix = 'INSERT INTO %s (' % table_name
        key_counter = 0
        for key in attributes.keys():
            if key_counter < len(attributes.keys()) - 1:
                statement_prefix += '%s, ' % key
            else:
                statement_prefix += '%s) VALUES ' % key
            key_counter += 1
        for counter in range(0, len(data[0])):
            statement = statement_prefix + '('
            attribute_counter = 0
            for data_param in data:
                value = str(data_param[counter])
                if value == 'nan':
                    value = 'NULL'
                if attribute_counter == 0:
                    value = '\'%s 00:00:00\'' % value
                if attribute_counter < len(data)-1:
                    statement += '%s, ' % value
                else:
                    # if counter < len(data[0])-1:
                    #     statement += '%s),' % value
                    # else:
                    statement += '%s);' % value
                attribute_counter += 1
            self.cursor.execute(statement)
        self.db.commit()
