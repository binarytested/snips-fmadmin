#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
from pyfmadmin import pyfmadmin

CONFIG_INI = "config.ini"

# If this skill is supposed to run on the satellite,
# please get this mqtt connection info from <config.ini>
# Hint: MQTT server is always running on the master device
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

class snips_fmadmin(object):
    """Class used to wrap action code with mqtt connection
        
        Please change the name refering to your application
    """

    def __init__(self):
        # get the configuration if needed
        try:
            self.config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
        except :
            self.config = None
                
        fa = pyfmadmin (str(self.config["secret"]["hostname"]), str(self.config["secret"]["username"]), str(self.config["secret"]["password"]))

        # start listening to MQTT
        self.start_blocking()
        
        
    def getIntentName (self, intent_message):
        intentName = intent_message.intent.intent_name
        intentName = intentName.split(":")[1]
        return intentName
        
        
    # --> Sub callback function, one per intent
    def connect_to_server(self, hermes, intent_message):

        loginResponse = self.fa.login()
        
        if loginResponse["result"] == 0:
	        print ( "Login successful!" )
	        #hermes.publish_start_session_notification(intent_message.site_id, "Connected to server", "")
	        hermes.publish_end_session(intent_message.session_id, "Connected to server")
        else:
	        print ( "Login failed" )
	        hermes.publish_end_session(intent_message.session_id, "Unable to connect to server")


        # if need to speak the execution result by tts
        #hermes.publish_start_session_notification(intent_message.site_id, "Action1 has been done", "")




    def disconnect_from_server(self, hermes, intent_message):
        # terminate the session first if not continue
        hermes.publish_end_session(intent_message.session_id, "")

        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        # if need to speak the execution result by tts
        hermes.publish_start_session_notification(intent_message.site_id, "Action2 has been done", "")

    # More callback function goes here...





    # --> Master callback function, triggered everytime an intent is recognized
    def master_intent_callback(self,hermes, intent_message):
        #coming_intent = intent_message.intent.intent_name
        coming_intent = self.getIntentName(intent_message)
        if coming_intent == 'connect_to_server':
            self.connect_to_server(hermes, intent_message)
        if coming_intent == 'intent_2':
            self.disconnect_from_server(hermes, intent_message)

        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.master_intent_callback).start()

if __name__ == "__main__":
    snips_fmadmin()
