#/usr/bin/python

# Tony Cheng <tony.pig@gmail.com>
# Version : 0.1
# Licensed under the Apache License, Version 2.0

import Adafruit_DHT
import sys
import datetime
import time
import influxdb
import pdb

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBServerError

db_host = '192.168.178.2'
db_port = 8086
db_user = ''
db_password = ''
db_name = 'iot'
db_hat_measurement = 'hat'

sleep_time = 30
hold_time = 3

hat_pin = '4'

def humidity_and_temperature_read(sensor, pin):
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    if humidity is not None and temperature is not None:
        print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))
    else:
        temperature = 'N/A'
        humidity = 'N/A'
    return format(temperature, '.4f'), format(humidity, '.4f')


def connect_db(host, port, user, password, dbname):
    try:
        client = InfluxDBClient(host, port, user, password)
        database = client.get_list_database()
        ''' client.get_list_database()
            e.g. [{u'name': u'_internal'}, {u'name': u'monasca'}]
            <type 'list'>
        '''
        db_exist = False
        for current_dbname in database:
            item = current_dbname
            if dbname in (item[u'name']):
                print("Database: %s is exist, switch database to %s") % (dbname, dbname)
                db_exist = True
                client.switch_database(dbname)
                print("DB connected")
                return client
        if not db_exist:
            print("DB is not exist, trying to create database.....")
            client.create_database(dbname)
            print("DB %s created, trying to switch database") % dbname
            client.switch_database(dbname)
            return client
    except influxdb.client.InfluxDBClientError as e:
        raise Exception(str(e))

def hat_write_db(client, measurement_name, temperature, humidity):
    #timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    json_body = [
    {
        "measurement": measurement_name,
        "tags": {
            "location": "Gobin-4F12",
            "place": "Compute Desktop",
        },
        "fields": {
            "temperature": temperature,
            "humidity": humidity
        }
    }
    ]
    print("Write points: {0}".format(json_body))

    try:
        client.write_points(json_body)
    except InfluxDBServerError as e_influxdbserver_err:
        #pdb.set_trace()
        if '503' in e_influxdbserver_err.message:
            time.sleep(hold_time)
            print("Caught '503 Service Unavailable' exception, need to wait and retry again.....")
            client.write_points(json_body)

def check_db_result(client):
    db_count_stmt = 'SELECT COUNT(result) FROM /./'
    points_count_raw = client.query(db_count_stmt)
    print("Acutal write points: {0}".format(points_count_raw))

if __name__ == '__main__':
    sn = 0
    client = connect_db(host=db_host, port=db_port, user=db_user, password=db_password, dbname=db_name)
    if True:
        print "Start : %s" % time.ctime()
        try:
            while True:
                sn+=1
                hat_result = humidity_and_temperature_read(Adafruit_DHT.AM2302, hat_pin)
                hat_write_db(client, db_hat_measurement, hat_result[0], hat_result[1])
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("End : %s") % time.ctime()
            print("Total write points: %i") % sn
            check_db_result(client)
