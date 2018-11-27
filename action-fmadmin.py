#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
from pyfmadmin import pyfmadmin

CONFIG_INI = "config.ini"

INTENT_DISCONNECT = "multip:disconnect_from_server"
INTENT_AMOUNT_USERS = "multip:amount_users_connected"
INTENT_FIND_USER = "multip:find_connected_user"

INTENT_FILTER = [
    INTENT_DISCONNECT,
    INTENT_AMOUNT_USERS,
    INTENT_FIND_USER
]

# If this skill is supposed to run on the satellite,
# please get this mqtt connection info from <config.ini>
# Hint: MQTT server is always running on the master device
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))



class snips_fmadmin(object):


    def __init__(self):
        # get the configuration if needed
        try:
            self.config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
        except :
            self.config = None
                
        self.fa = pyfmadmin (str(self.config["secret"]["hostname"]), str(self.config["secret"]["username"]), str(self.config["secret"]["password"]))

        # start listening to MQTT
        self.start_blocking()
        
        
    def getIntentName (self, intent_message):
        intentName = intent_message.intent.intent_name
        intentName = intentName.split(":")[1]
        return intentName
        
        
    # --> Sub callback function, one per intent
    def connect_to_server(self, hermes, intent_message):

        #hermes.publish_start_session_notification(intent_message.site_id, "Attempting connection to server...", "")
        
        loginResponse = self.fa.login()
        
        if loginResponse["result"] == 0:
	        print ( "Login successful!" )
	        hermes.publish_continue_session(intent_message.session_id, "Connected to server. What would you like to do?", INTENT_FILTER)
	        #hermes.publish_end_session(intent_message.session_id, "Connected to server")
        else:
	        print ( "Login failed" )
	        hermes.publish_end_session(intent_message.session_id, "Unable to connect to server")


        # if need to speak the execution result by tts
        #hermes.publish_start_session_notification(intent_message.site_id, "Action1 has been done", "")




    def disconnect_from_server(self, hermes, intent_message):
        hermes.publish_end_session(intent_message.session_id, "Disconnecting from server")
        
        logoutResponse = self.fa.logout()
        
        if logoutResponse["result"] == 0:
	        print ( "Logout successful!" )
        else:
	        print ( "Logout failed" )

        # if need to speak the execution result by tts
        #hermes.publish_start_session_notification(intent_message.site_id, "Action2 has been done", "")



    def amount_users_connected(self, hermes, intent_message):
        databaseDict = self.fa.list_databases()
        
        # get client dictionary
        clientDict = databaseDict["clients"]["clients"]
        
        # count client items
        clientCount = len(clientDict)
        
        if clientCount == 0:
            sentence = "There are currently no users connected"
        if clientCount == 1:
            sentence = "There is currently only one user connected"
        else:
            sentence = "There are currently " + str(clientCount) + " users connected"
        
        hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)



    def find_connected_user(self, hermes, intent_message):

        #slotItems = intent_message.slots.items()
        #username = intent_message.slots.items()
        
        #print("Username: " + str(username))
        print("Items: " + intent_message.slots.items())
        
        sentence = "Finding user"
        
        hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)




    # More callback function goes here...





    # --> Master callback function, triggered everytime an intent is recognized
    def master_intent_callback(self,hermes, intent_message):
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)
        #coming_intent = intent_message.intent.intent_name
        coming_intent = self.getIntentName(intent_message)
        if coming_intent == 'connect_to_server':
            self.connect_to_server(hermes, intent_message)
        if coming_intent == 'disconnect_from_server':
            self.disconnect_from_server(hermes, intent_message)
        if coming_intent == 'amount_users_connected':
            self.amount_users_connected(hermes, intent_message)
        if coming_intent == 'find_connected_user':
            self.find_connected_user(hermes, intent_message)


        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.master_intent_callback).start()

if __name__ == "__main__":
    snips_fmadmin()
