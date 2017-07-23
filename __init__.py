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

##from contextlib2 import suppress
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


blueprint = Blueprint('one_wire_bp', __name__)

def getBPSSRs():
    try:
        arr = []
        for dirname in os.listdir('/sys/bus/w1/devices'):
            if (dirname.startswith("3a")):
                arr.append(dirname)
        return arr
    except:
        return []


def setBPstate(actor, state):
    with ignored(Exception):
        with open('/sys/bus/w1/devices/%s/output' % (actor), 'wb') as fo:
            fo.write(struct.pack("=B",state))
            ##return True
    ##return False


def getBPstate(actor):
    b = None
    with ignored(Exception):
        with open('/sys/bus/w1/devices/w1_bus_master1/%s/state' % actor, 'rb') as cf:
            b=cf.read(1)
    return b


@cbpi.actor
class BrewPiSSR(ActorBase):
    actor_name = Property.Select("Name", options=getBPSSRs(), description="The OneWire SSR address.")
    port_name  = Property.Select("Port", options=["A","B"], description="The OneWire SSR port.")

    curr_act = 0  ## porta and b off
    n_cur=3
    n=3
    acta_cur=0
    actb_cur=0

    def curr_state(self):
        b=getBPstate(self.actor_name)

        # find status port A + B
        if b:
            if (ord(b) & 2):
                self.acta_cur = 0  ## porta off
            else:
                self.acta_cur = 1  ## porta on
            if (ord(b) & 8):
                self.actb_cur = 0  ## portb off
            else:
                self.actb_cur = 1  ## portb on
        return 3-(self.acta_cur+self.actb_cur+self.actb_cur)

    def target_state_on(self):
        if (self.port_name == "A") and (self.actb_cur is 0):
            self.n = 2
        elif (self.port_name == "A") and (self.actb_cur is 1):
            self.n = 0
        elif (self.port_name == "B") and (self.acta_cur is 0):
            self.n = 1
        elif (self.port_name == "B") and (self.acta_cur is 1):
            self.n = 0
        else:
            self.n = 255
        return self.n


    def target_state_off(self):
        if self.port_name == "A" and self.actb_cur is 0:
            self.n = 3
        elif self.port_name == "A" and self.actb_cur is 1:
            self.n = 1
        elif self.port_name == "B" and self.acta_cur is 0:
            self.n = 3
        elif self.port_name == "B" and self.acta_cur is 1:
            self.n = 2
        else:
            self.n = 255
        return self.n


    def init(self):
        #init place for routines
        ##actor_name = Property.Select("Name", options=self.getBPSSRs(self), description="The OneWire SSR address.")
        ##port_name  = Property.Select("Port", options=["A","B"], description="The OneWire SSR port.")
        ##cbpi.app.logger.info("BrewPiSSR Name: %s 1W: %s PORT: %s" % (self.name, self.actor_name, self.port_name))
        ##cbpi.app.logger.info("INIT BrewPiSSR %s ON %s PORT: %s" % (self.name, self.actor_name, self.port_name))
        ##print "INIT BrewPiSSR ON %s PORT: %s" % (self.actor_name, self.port_name)
        pass

    def on(self, power=100):
        ##print "SWITCH %s ON %s PORT: %s" % (self.name, self.actor_name, self.port_name)
        cbpi.app.logger.info("SWITCH %s ON %s PORT: %s" % (self.name, self.actor_name, self.port_name))
        if self.actor_name is None:
            return

        n_cur = self.curr_state()
        n = self.target_state_on()
        
        setBPstate(self.actor_name,n)


    def off(self):
        ##print "SWITCH OFF %s PORT: %s" % (self.actor_name, self.port_name)
        cbpi.app.logger.info("SWITCH %s OFF %s PORT: %s" % (self.name, self.actor_name, self.port_name))
        if self.actor_name is None:
            return

        n = self.target_state_off()
        setBPstate(self.actor_name,n)


    @classmethod
    def init_global(cls):
        print "GLOBAL %s ACTOR" % (cls.__name__)
        try:
            call(["modprobe", "w1-gpio"])
            call(["modprobe", "w1-ds2413"])
        except Exception as e:
            pass

