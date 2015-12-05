# -*- coding: utf-8 -*-

# Questa classe rimane in ascolto su una porta, per messaggi codificati, li decomprime, li invia al MULE, riceve le
# risposte e le restituisce alle centraline
#
#        +------+                   +------------+                   +------+
#        | BBox |------------------>|     Me     |------------------>| MULE |
#        |      |<------------------|            |<------------------|      |
#        +------+                   +------------+                   +------+
# http://krondo.com/wp-content/uploads/2009/08/twisted-intro.html

from twisted.internet.protocol import DatagramProtocol
from twisted.web.client import getPage
from twisted.internet import reactor
import binascii
import time
import os
import sys
from ControlUnit import ControlUnit


class BBoxDecoder(DatagramProtocol):
    """Riceve un messaggio compresso dalle centraline e lo spedisce al server"""

    C_TXS_URL = "http://151.1.80.42/src/api/v1?rawData="
    C_OUT_PATH = "/mnt/nas/temp/"
    C_OUT_FILE = "/mnt/nas/temp/fuelcheck_traslator.log"

    def __init__(self):

        self.ctrl_unit = ControlUnit()

        if os.path.isdir(self.C_OUT_PATH):
            self.can_log = True
            print("Log path found")
        else:
            self.can_log = False
            print("Log path not found")

        print "Starting ControlUnit binary receiver v0.1a"

    def log_data(self, date, imei, hex_data, host, port, comment):

        if self.can_log:
            with open(self.C_OUT_FILE, 'a') as f:
                f.write(
                    "{0};{1};{2};{3};{4};{5}\n".format(
                        date,
                        imei,
                        hex_data,
                        host,
                        port,
                        comment
                    )
                )

    def print_page(self, result, host, port, data, ctrl_unit):
        print "  MULE say {}".format(result)
        self.log_data(
            time.strftime("%d %b %H:%M:%S", time.gmtime(ctrl_unit.unixtime)),
            ctrl_unit.imei,
            binascii.hexlify(data).upper(),
            host,
            port,
            result
        )
        self.transport.write(result, (host, port))

    def print_error(self, failure, host, port, data, ctrl_unit):
        print "  MULE say EPIC FAIL! {} - {}".format(sys.stderr, failure)
        self.log_data(
            time.strftime("%d %b %H:%M:%S", time.gmtime(ctrl_unit.unixtime)),
            ctrl_unit.imei,
            binascii.hexlify(data).upper(),
            host,
            port,
            failure
        )

    def datagramReceived(self, data, (host, port)):

        # Evento: mi è appena arrivato un pacchetto binario dalle centraline
        print("Received {} from {}:{}".format(binascii.hexlify(data), host, port))

        # La decodifico da binario in variabili interne
        try:
            self.ctrl_unit.decode_binary(data)
        except (ValueError, TypeError):
            print("  - Conversion error")
            self.log_data(
                "",
                "",
                binascii.hexlify(data).upper(),
                host,
                port,
                "Conversion error"
            )

        # Se i dati sono validi
        if self.ctrl_unit.check_values():

            self.log_data(
                time.strftime("%d %b %H:%M:%S", time.gmtime(self.ctrl_unit.unixtime)),
                self.ctrl_unit.imei,
                binascii.hexlify(data).upper(),
                host,
                port,
                "OK"
            )

            # Li codifico in ASCII
            try:
                self.ctrl_unit.encode_ascii()
            except (ValueError, TypeError):
                print("  - Encoding error")
                self.log_data(
                    "",
                    "",
                    binascii.hexlify(data).upper(),
                    host,
                    port,
                    "Encoding error"
                )

            print("  Coded {}".format(self.ctrl_unit.output_packet))
            self.log_data(
                time.strftime("%d %b %H:%M:%S", time.gmtime(self.ctrl_unit.unixtime)),
                self.ctrl_unit.imei,
                binascii.hexlify(data).upper(),
                host,
                port,
                self.ctrl_unit.output_packet
            )

            # Li invio al server MULE, e quando sarà pronta la risposta faccio chiamare printPage o printError
            d = getPage(self.C_TXS_URL + self.ctrl_unit.output_packet)
            d.addCallback(self.print_page, host, port, data, self.ctrl_unit)
            d.addErrback(self.print_error, host, port, data, self.ctrl_unit)
            # d.addBoth(stop)

        else:
            self.log_data(
                "",
                "",
                binascii.hexlify(data).upper(),
                host,
                port,
                "Value error"
            )

if __name__ == '__main__':

    reactor.listenUDP(9123, BBoxDecoder())
    reactor.run()
