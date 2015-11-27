# -*- coding: utf-8 -*-
from ControlUnit import ControlUnit
import time
import math
import datetime
import calendar

class AsciiProtocol(ControlUnit):
    """Classe per la codifica e decodifica del protocollo ASCII attualmente implementato"""

    def __init__(self):

        ControlUnit.__init__(self)

        self.header = "A5"                    # Always A5
        self.version = 1

    def encode(self):
        """Prende una serie di variabili e ne crea un messaggio codificato in ASCII"""

        # Bisogna controllare tutti i parametri in ingresso
        try:
            self.check_values()
        except:
            raise

        # Converto la data in struct_time UTC
        s_time = time.gmtime(self.unixtime)

        # Converto la latitudine
        temp = math.modf(self.lat)
        if self.lat > 0:
            lat_final = "{:02.0f}{:06.0f}N".format(temp[1],round(temp[0]*600000))
        else:
            lat_final = "{:02.0f}{:06.0f}S".format(temp[1],round(temp[0]*600000))
        # Converto la longitudine
        temp = math.modf(self.lon)
        if self.lon > 0:
            lon_final = "{:03.0f}{:06.0f}E".format(temp[1],round(temp[0]*600000))
        else:
            lon_final = "{:03.0f}{:06.0f}W".format(temp[1],round(temp[0]*600000))

        output_packet = self.header
        output_packet += "00"
        output_packet += "{:02X}".format(1)
        output_packet += self.imei
        output_packet += "{:04d}".format(self.driver)
        output_packet += "{:02X}".format(self.event)
        output_packet += time.strftime("%Y%m%d%H%M%S", s_time)
        output_packet += "{:02d}".format(self.sat)
        output_packet += "{:s}".format(lat_final)
        output_packet += "{:s}".format(lon_final)
        output_packet += "{:04.0f}".format(self.speed*10)
        output_packet += "{:04.0f}".format(self.gasoline_r*10)
        output_packet += "{:04.0f}".format(self.gasoline_l*10)
        output_packet += "{:04.0f}".format(self.gasoline_f*10)
        output_packet += "{:03.0f}".format(self.vin*10)
        output_packet += "{:03.0f}".format(self.vbatt*100)
        output_packet += "{:04.0f}".format(self.input_gasoline_r*10)
        output_packet += "{:04.0f}".format(self.input_gasoline_l*10)
        output_packet += "{:04.0f}".format(self.input_gasoline_f*10)
        output_packet += "{:04.0f}".format(self.input_gasoline_tot)
        output_packet += "{:01d}".format(self.cup_r)
        output_packet += "{:01d}".format(self.cup_l)
        output_packet += "{:01d}".format(self.cup_f)
        output_packet += "{:01d}".format(self.engine)
        output_packet += "UUUU"
        output_packet += "{:01d}".format(self.alarm)
        output_packet += "{:01d}".format(self.cup_lock)
        output_packet += "UUUUUU"
        output_packet += "{:05.0f}".format(self.distance_travelled*10)

        if len(output_packet) != 121:
            return False

        # Calcolo la lunghezza e la inserisco in esadecimale
        output_packet = output_packet[0:2] + "{:02X}".format(len(output_packet)) + output_packet[4:]

        self.output_packet = output_packet

        return True

    def decode(self, input_message):
        """Prende un messaggio codificato in ASCII e ne ricava tutte le variabili"""

        # Controllo l'header
        if input_message[0:2] != "A5":
            raise ValueError("Campo header errato ({:2s} != A5)".format(input_message[0:2]))

        # Controllo la lunghezza del pacchetto
        if len(input_message) != int(input_message[2:4], 16):
            raise ValueError("Campo lunghezza stringa errato ({:02X} != 0x79)".format(len(input_message)))

        # Controllo versione software
        if input_message[4:6] != "01":
            raise ValueError("Campo versione errato ({:02X} != 01)".format(int(input_message[4:6])))

        # Controllo IMEI
        if not input_message[6:21].isdigit():
            raise ValueError("Campo IMEI non contiene solo numeri: ({:15s})".format(input_message[6:21]))

        # Controllo Autista
        if not input_message[21:25].isdigit():
            raise ValueError("Campo Autista non contiene solo numeri: ({:4s})".format(input_message[21:25]))

        # Controllo Evento (compreso tra 0 ed FF)
        if not 0 < int(input_message[25:27], 16) < 255 or input_message[25:27].islower():
            raise ValueError("Campo Evento non esadecimale maiuscolo: ({:2s})".format(input_message[25:27]))

        # Controllo data YYYYMMDD
        if not input_message[27:35].isdigit():
            raise ValueError("Formato data non corretto presenza di caratteri: ({:8s})".format(input_message[27:35]))
        try:
            datetime.datetime.strptime(input_message[27:35], '%Y%m%d')
        except ValueError:
            raise ValueError("Formato data non corretto: ({:8s})".format(input_message[27:35]))

        # Controllo ora
        if not input_message[35:41].isdigit():
            raise ValueError("Formato ora non corretto presenza di caratteri: ({:8s})".format(input_message[35:41]))
        try:
            datetime.datetime.strptime(input_message[35:41], '%H%M%S')
        except ValueError:
            raise ValueError("Formato ora non corretto: ({:6s})".format(input_message[35:41]))

        # Controllo satelliti
        if not input_message[41:43].isdigit():
            raise ValueError("Formato satelliti non corretto presenza di caratteri: ({:2s})".format(input_message[41:43]))

        # Controllo latitudine
        if not input_message[43:51].isdigit():
            raise ValueError("Formato latitudine non corretto presenza di caratteri: ({:9s})".format(input_message[43:52]))
        if not -90 <= int(input_message[43:45], 10) <= 90:
            raise ValueError("Formato latitudine non corretto fuori range +/-90°: ({:9s})".format(input_message[43:52]))
        if int(input_message[45:47], 10) >= 60:
            raise ValueError("Formato latitudine non corretto fuori range > 59': ({:9s})".format(input_message[43:52]))
        if input_message[51] != 'N' and input_message[51] != 'S':
            raise ValueError("Formato latitudine non corretto != N/S ({:9s})".format(input_message[43:52]))

        # Controllo longitudine
        if not input_message[52:61].isdigit():
            raise ValueError("Formato latitudine non corretto presenza di caratteri: ({:10s})".format(input_message[52:62]))
        if not -180 <= int(input_message[52:55], 10) <= 180:
            raise ValueError("Formato latitudine non corretto fuori range +/-180°: ({:10s})".format(input_message[52:62]))
        if int(input_message[55:57], 10) >= 60:
            raise ValueError("Formato latitudine non corretto fuori range > 59': ({:10s})".format(input_message[52:62]))
        if input_message[61] != 'E' and input_message[61] != 'W':
            raise ValueError("Formato latitudine non corretto != E/W ({:9s})".format(input_message[52:62]))

        # Controllo velocita'
        if not input_message[62:66].isdigit():
            raise ValueError("Formato velocita' non corretto presenza di caratteri: ({:4s})".format(input_message[62:66]))

        # Controllo litri serbatoio DX
        if not input_message[66:70].isdigit():
            raise ValueError("Formato litri DX non corretto presenza di caratteri: ({:4s})".format(input_message[66:70]))

        # Controllo litri serbatoio SX
        if not input_message[70:74].isdigit():
            raise ValueError("Formato litri SX non corretto presenza di caratteri: ({:4s})".format(input_message[70:74]))

        # Controllo litri serbatoio Frigo
        if not input_message[74:78].isdigit():
            raise ValueError("Formato litri FR non corretto presenza di caratteri: ({:4s})".format(input_message[74:78]))

        self.imei = input_message[6:21]               # Inserisco l'IMEI verificato nella variabile imei
        self.driver = input_message[21:25]            # Inserisco l'autista verificato nella variabile driver
        self.event = input_message[25:27]             # Inserisco l'evento verificato nella variabile event

        # genero la stringa contenente YYYYMMDD e HHMMSS
        s_data = input_message[27:31] + \
                 input_message[31:33] + \
                 input_message[33:35] + \
                 input_message[35:37] + \
                 input_message[37:39] + \
                 input_message[39:41]
        self.unixtime = calendar.timegm(datetime.datetime.strptime(s_data, "%Y%m%d%H%M%S").timetuple())
        self.sat = input_message[41:43]

        if input_message[51] == 'N':
            self.lat = float(input_message[43:45]) + float(input_message[45:51])/600000
        else:
            self.lat = -(float(input_message[43:45]) + float(input_message[45:51])/600000)
        if input_message[61] == 'E':
            self.lon = float(input_message[52:55]) + float(input_message[55:61])/600000
        else:
            self.lon = -(float(input_message[52:55]) + float(input_message[55:61])/600000)

        self.speed = (float(input_message[62:66])/10)
        self.gasoline_r = (float(input_message[66:70])/10)
        self.gasoline_l = (float(input_message[70:74])/10)
        self.gasoline_f = (float(input_message[74:78])/10)

        return True