# -*- coding: utf-8 -*-
import os, sys, getopt, struct
from subprocess import Popen, PIPE, call
from struct import *
from modules import cbpi, app
from modules.core.hardware import SensorPassive, SensorActive
import json
import re, threading, time
from flask import Blueprint, render_template, request
from modules.core.props import Property
from modules.core.hardware import ActorBase 

try:
    from contextlib import contextmanager
except Exception as e:
    cbpi.notify("Initialize BrewPiSSR failed", "Please make sure to run: sudo apt-get install contextlib", type="danger", timeout=None)
    pass

@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


try:
    from pyowfs import Connection
    root = Connection('localhost:4304')
except Exception as e:
    root = None
    pass


blueprint = Blueprint('one_wire_bp_ssr', __name__)


@cbpi.actor
class BrewPiSSR(ActorBase):
    ##global root    # Needed to modify global copy of root

    def getBPSSRs():
        try:
            arr = []
            for dirname in os.listdir('/sys/bus/w1/devices'):
                if (dirname.startswith("3a")):
                    cbpi.app.logger.info("Device Found (SSR on GPIO4)")
                    cbpi.app.logger.info("Address: %s" % dirname)
                    cbpi.app.logger.info("Family: %s" % "3A")
                    cbpi.app.logger.info(" ")
                    arr.append(dirname)
        except:
            pass

        try:
            if root != None:
                for s in root.find (family="3A"): 
                    cbpi.app.logger.info("Device Found (SSR on owfs)")
                    cbpi.app.logger.info("Address: %s" % s.get("address"))
                    cbpi.app.logger.info("Family: %s"  % s.get("family"))
                    cbpi.app.logger.info("ID: %s"      % s.get("id"))
                    cbpi.app.logger.info("Type: %s"    % s.get("type"))
                    cbpi.app.logger.info(" ")
                    arr.append(s.get("address"))
            return arr
        except:
            return []


    actor_name = Property.Select("Name", options=getBPSSRs(), description="The OneWire SSR address.")
    port_name  = Property.Select("Port", options=["A","B"], description="The OneWire SSR port.")


    def getBPstate(self, actor, port):
        with ignored(Exception):
            if root != None:
                for s in root.find (address=actor):
                    if list(s)[0] == None:
                        self.OWFS = False
                    else:
                        self.OWFS = True
            else:
                self.OWFS = False 

            if self.OWFS == False:
                with open('/sys/bus/w1/devices/w1_bus_master1/%s/state' % actor, 'rb') as cf:
                    b = cf.read(1)
                # find status port A + B
                if (port == "A"):
                    if (ord(b) & 2):
                         return ("OFF")  ## porta off
                    else:
                         return ("ON")   ## porta on
                if (port == "B"):
                    if (ord(b) & 8):
                         return ("OFF")  ## portb off
                    else:
                         return ("ON")   ## portb on
            else:
                s = root.find(address=actor)[0]
                s.use_cache (0)
                key = "PIO.BYTE"
                if (s.has_key (key)):
                    x = s.get(key)
                st = list(x)[0]
                if (st == 0x03):
                    sta = "ON"
                    stb = "ON"
                if (st == 0x00):
                    sta = "OFF"
                    stb = "OFF"
                if (st == 0x01):
                    sta = "ON"
                    stb = "OFF"
                if (st == 0x02):
                    sta = "OFF"
                    stb = "ON"
                ##cbpi.app.logger.info("SSR: %s, port: %s, stata: %s, statb: %s" % (actor, port, sta, stb))
                if (port == "A"):
                    return (sta)
                if (port == "B"):
                    return (stb)
        return ("OFF")


    def setBPstate(self, actor, port, state):
        with ignored(Exception):
            if root != None:
                if (root.find(address=actor)):
                    self.OWFS = True
                else:
                    self.OWFS = False
            else:
                self.OWFS = False 

            if self.OWFS == False:
                if (port == "A"):
                    stb = self.getBPstate(actor,"B")
                    sta = state
                if (port == "B"):
                    sta = self.getBPstate(actor,"A")
                    stb = state
                cbpi.app.logger.info("SSR: %s, port: %s, stata: %s, statb: %s" % (actor, port, sta, stb))
                ##if (sta == "ON") and (stb =="ON"):
                ##    st = 0x00
                ##if (sta == "ON") and (stb =="OFF"):
                ##    st = 0x02
                ##if (sta == "OFF") and (stb =="ON"):
                ##    st = 0x01
                ##if (sta == "OFF") and (stb =="OFF"):
                ##    st = 0xff
                if (sta == "ON") and (stb == "ON"):
                    st = 0x00
                if (sta == "ON") and (stb == "OFF"):
                    st = 0x02
                if (sta == "OFF") and (stb == "ON"):
                    st = 0x01
                if (sta == "OFF") and (stb == "OFF"):
                    st = 0x03
                with ignored(Exception):
                    ##cbpi.app.logger.info("SSR: %s, port: %s, %s Just before write." % (actor, port, state))
                    with open('/sys/bus/w1/devices/%s/output' % (actor), 'wb') as fo:
                        fo.write(struct.pack("=B",st))
                ##cbpi.app.logger.info("SSR: %s, port: %s, %s" % (actor, port, state))
            else:
                s=root.find(address=actor)[0]
                if (port == "A"):
                    key = "PIO.A"
                    stb = self.getBPstate(actor,"B")
                    sta = state
                if (port == "B"):
                    key = "PIO.B"
                    sta = self.getBPstate(actor,"A")
                    stb = state
                ##key="PIO.BYTE"
                if (s.has_key (key)):
                    ##cbpi.app.logger.info("SSR: %s, port: %s, stata: %s, statb: %s" % (actor, port, sta, stb))
                    if (sta == "ON") and (stb =="ON"):
                        st = 0x03
                    if (sta == "ON") and (stb =="OFF"):
                        st = 0x01
                    if (sta == "OFF") and (stb =="ON"):
                        st = 0x02
                    if (sta == "OFF") and (stb =="OFF"):
                        st = 0x00
                    ##cbpi.app.logger.info("SSR: %s, port: %s, sta: %04x" % (actor, port, st))
                    x = s.put(key,st)
            pass


    def init(self):
        #init place for routines
        pass


    def on(self, power=100):
        cbpi.app.logger.info("SWITCH %s (%s) PORT: %s ON" % (self.name, self.actor_name, self.port_name))
        if self.actor_name is None:
            return
        self.setBPstate(self.actor_name, self.port_name, "ON")


    def off(self):
        cbpi.app.logger.info("SWITCH %s (%s) PORT: %s OFF" % (self.name, self.actor_name, self.port_name))
        if self.actor_name is None:
            return
        self.setBPstate(self.actor_name, self.port_name, "OFF")


    @classmethod
    def init_global(cls):
        print "GLOBAL %s ACTOR" % (cls.__name__)
        try:
            call(["modprobe", "w1-gpio"])
            call(["modprobe", "w1-ds2413"])
        except Exception as e:
            pass

