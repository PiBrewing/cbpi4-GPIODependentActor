
# -*- coding: utf-8 -*-
import os
from aiohttp import web
import logging
from unittest.mock import MagicMock, patch
import asyncio
import random
from cbpi.api import *
from cbpi.api.dataclasses import NotificationAction, NotificationType
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

@parameters([Property.Actor(label="Actor",  description="Select the actor that will be switched off depending on the GPIO state."),
            Property.Select(label="GPIO", options=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27], description="GPIO [BMC numbering] that will switch off the Actor"), 
            Property.Select(label="GPIOstate", options=["High", "Low"],description="High: Actor switches off on GPIO high; Low: Actor switches off on GPIO low"),
            Property.Select(label="notification", options=["Yes", "No"], description="Will show notification when GPIO switches actor off")])

class GPIODependentActor(CBPiActor):

    async def wait_for_input(self):
        while True:
            inputsignal=GPIO.input(int(self.ActorDependency))
            logging.info(inputsignal)
            if (self.dependency_type == "High") and (GPIO.input(int(self.ActorDependency))):
                logging.info("Break on high")
                await self.off()
                self.state = False
                if self.notification == "Yes":
                    self.cbpi.notify("GPIO Dependent Actor", "Actor {} switched off as GPIO {} siwtchted to {}".format(self.name, self.ActorDependency, self.dependency_type), NotificationType.INFO)
                break
            elif (self.dependency_type == "Low") and not (GPIO.input(int(self.ActorDependency))):
                logging.info("Break on Low")
                await self.off()
                self.state = False
                if self.notification == "Yes":
                    self.cbpi.notify("GPIO Dependent Actor", "Actor {} switched off as GPIO {} siwtchted to {}".format(self.name, self.ActorDependency, self.dependency_type), NotificationType.INFO)
                break
            if self.interrupt == True:
                break
            await asyncio.sleep(1)

    def on_start(self):
        self.state = False
        self.base = self.props.get("Actor", None)
        try:
            self.name = (self.cbpi.actor.find_by_id(self.base).name)
        except:
            self.name = ""
        self.ActorDependency = self.props.get("GPIO", None)
        self.dependency_type = self.props.get("GPIOstate", "High")
        self.notification = self.props.get("notification", "Yes")
        self.interrupt = False
        mode = GPIO.getmode()
        logging.info(mode)
        if (mode == None):
            GPIO.setmode(GPIO.BCM)
        if self.ActorDependency is not None:
            GPIO.setup(int(self.ActorDependency), GPIO.IN)
        else:
            pass

        pass

    async def on(self, power=0):
        self.interrupt = False
        await self.cbpi.actor.on(self.base)
        self._task = asyncio.create_task(self.wait_for_input())
        self.state = True

    async def off(self):
        logger.info("ACTOR %s OFF " % self.base)
        await self.cbpi.actor.off(self.base)
        self.interrupt = True
        self.state = False

    def get_state(self):
        return self.state
    
    async def run(self):
        pass


def setup(cbpi):
    cbpi.plugin.register("GPIO Dependent Actor", GPIODependentActor)
    pass

