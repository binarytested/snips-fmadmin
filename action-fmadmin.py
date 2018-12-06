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
INTENT_FILES_USER_USING = "multip:files_user_is_using"
INTENT_DISCONNECT_CURRENT_USER = "multip:disconnect_current_user"
INTENT_CLOSE_CURRENT_DATABASES = "multip:close_current_databases"


INTENT_FILTER = [
    INTENT_DISCONNECT,
    INTENT_AMOUNT_USERS,
    INTENT_FIND_USER,
    INTENT_FILES_USER_USING,
    INTENT_DISCONNECT_CURRENT_USER,
    INTENT_CLOSE_CURRENT_DATABASES
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
        
        # init context awareness variables
        self.initContext()

        # start listening to MQTT
        self.start_blocking()
        
        
        
        
    def initContext(self):
        self.context_clients = []
        self.context_databases = []

        
    def clearContext(self):
        self.context_clients[:] = []
        self.context_databases[:] = []

   
   
    def setClientContext(self, clientItem):
        # clear current context
        self.context_clients[:] = []
        
        # set the current context depending on object type received
        if type(clientItem) is list:
            self.context_clients = clientItem
        if type(clientItem) is dict:
            self.context_clients.append(clientItem)


    def setDatabaseContext(self, databaseItem):
        # clear current context
        self.context_databases[:] = []
        
        # set the current context depending on object type received
        if type(databaseItem) is list:
            self.context_databases = databaseItem
        if type(databaseItem) is dict:
            self.context_databases.append(databaseItem)
            
 
    def closeDatabasesInContext(self, message=None):
        if len(self.context_databases) == 0:
            return
        
        errorCount = 0
        
        for database in self.context_databases:
            if database["status"] == "NORMAL":
                closeResponse = self.fa.close_database (database["id"], message=message)
                if closeResponse["result"] == 0:
                    print ( "    --> success: " + database["filename"] + " closed" )
                else:
                    errorCount = errorCount + 1
                    print ( "       " + closeResponse["description"] )
                    print ( "    --> fail: " + database["filename"] )

        return errorCount
                        
        
    def getIntentName(self, intent_message):
        intentName = intent_message.intent.intent_name
        intentName = intentName.split(":")[1]
        return intentName
        
        
        
        
    # --> Sub callback function
    # --> Log into server
    def connect_to_server(self, hermes, intent_message):

        #hermes.publish_start_session_notification(intent_message.site_id, "Attempting connection to server...", "")
        
        loginResponse = self.fa.login()
        
        if loginResponse["result"] == 0:
	        print ( "Login successful!" )
		h.subscribe_intents(self.master_intent_callback)
	        hermes.publish_continue_session(intent_message.session_id, "Connected to server. What would you like to do?", INTENT_FILTER)
	        #hermes.publish_end_session(intent_message.session_id, "Connected to server")
        else:
	        print ( "Login failed" )
	        hermes.publish_end_session(intent_message.session_id, "Unable to connect to server")


        # if need to speak the execution result by tts
        #hermes.publish_start_session_notification(intent_message.site_id, "Action1 has been done", "")



    # --> Sub callback function
    # --> Logout of server
    def disconnect_from_server(self, hermes, intent_message):
        #hermes.publish_end_session(intent_message.session_id, "Disconnecting from server")
        
        # clear context awareness variables
        self.clearContext()
                
        # logout of FMS
        logoutResponse = self.fa.logout()
        
        if logoutResponse["result"] == 0:
	        print ( "Logout successful!" )
        else:
	        print ( "Logout failed" )

        hermes.publish_end_session(intent_message.session_id, "Disconnecting from server")
        # if need to speak the execution result by tts
        #hermes.publish_start_session_notification(intent_message.site_id, "Action2 has been done", "")




    # --> Sub callback function
    # --> Reads amount of users currently connected
    def amount_users_connected(self, hermes, intent_message):
        databaseDict = self.fa.list_databases()
        
        # get client dictionary
        clientDict = databaseDict["clients"]["clients"]
        
        # changing context
        self.setClientContext(clientDict)
        
        # count client items
        clientCount = len(clientDict)
        
        if clientCount == 0:
            sentence = "There are currently no users connected"
        if clientCount == 1:
            sentence = "There is currently only one user connected"
        else:
            sentence = "There are currently " + str(clientCount) + " users connected"
        
        hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)




    # --> Sub callback function
    # --> Determine if a particular user is connected
    def find_connected_user(self, hermes, intent_message):
        databaseDict = self.fa.list_databases()
        
        # get client dictionary
        clientList = databaseDict["clients"]["clients"]
        
        usernameFind = str(intent_message.slots["person"][0].raw_value)
        
        
        for client in clientList:
            if usernameFind.lower() in client["userName"].lower():
                # found the user
                
                # changing client context
                self.setClientContext(client)
                
                fileIdList = []
                for file in self.context_clients[0]["guestFiles"]:
                    fileIdList.append(file["id"])

                # change database context
                databaseList = databaseDict["files"]["files"]
                databaseList[:] = [database for database in databaseList if database["id"] in fileIdList]
                self.context_databases = databaseList
                print (databaseList)
                
                fileCount = len(client["guestFiles"])
                
                if fileCount == 1:
                    fileOpenStr = " only one file open"
                else:
                    fileOpenStr = str(fileCount) + " files open"
                    
                sentence = "yes, " + usernameFind + " seems to be connected as " + client["userName"] + ", and has " + fileOpenStr
                break
        else:
            # did not find the user
            sentence = "No, I don't see " + usernameFind + " at this time"
            
        hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)




    # --> Sub callback function
    # --> Reads list of files user is using. Client context is single
    def files_user_is_using(self, hermes, intent_message):
        # exit if context is inappropriate
        if len(self.context_clients) == 0:
            sentence = "Sorry. I'm not sure who you're talking about"
            hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)
            return
        if len(self.context_clients) > 1:
            sentence = "Sorry. There seems to be a misunderstanding regarding who we're talking about"
            hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)
            return        
            
        fileNameList = []
        fileIdList = []
        for file in self.context_clients[0]["guestFiles"]:
            fileNameList.append(file["filename"].replace(".fmp12",""))
            fileIdList.append(file["id"]) 
        
        # change context
        databaseDict = self.fa.list_databases()
        databaseList = databaseDict["files"]["files"]
        databaseList[:] = [database for database in databaseList if database["id"] in fileIdList]
        self.context_databases = databaseList
        print (databaseList)


        fileNames = ", ".join( fileNameList )
        username = self.context_clients[0]["userName"]
        sentence = username + " is currently using the following files: " + fileNames
        
        hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)

        


    # --> Sub callback function
    # --> Disconnects the current context user. Client context is single
    def disconnect_current_user(self, hermes, intent_message):
        # exit if context is inappropriate
        if len(self.context_clients) == 0:
            sentence = "Sorry. I'm not sure who you're talking about"
            hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)
            return
        if len(self.context_clients) > 1:
            sentence = "Sorry. There seems to be a misunderstanding regarding who we're talking about"
            hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)
            return


        # user variable
        client_id = self.context_clients[0]["id"]
        username = self.context_clients[0]["userName"]

        # set optional parameters
        #gracetime = 10
        slot = intent_message.slots["gracetime"]
        gracetime = slot[0].slot_value.value.seconds
        gracetime = gracetime + (slot[0].slot_value.value.minutes * 60)
        gracetime = gracetime + (slot[0].slot_value.value.hours * 3600)
        #print ( "    --> gracetime: " + str(gracetime) )
        message = "Please close all files. You will be automatically disconnected in " + str(gracetime) + " seconds."

        disconnectResponse = self.fa.disconnect_client (client_id, message=message, gracetime=gracetime)
        if disconnectResponse["result"] == 0:
	        #print ( "    --> success <--" )
	        sentence = "I sent " + username + " the disconnect notice"
        else:
	        #print ( "    --> fail <--" )
	        sentence = "There was an error sending the disconnect notice"

        hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER)




    # --> Sub callback function
    # --> Close the current context database files. Database context is plural
    def close_current_databases(self, hermes, intent_message):
        message = "This file is being closed by the administrator."
        errorCount = self.closeDatabasesInContext(message)
        
        if errorCount == 0:
            sentence = "Files closed."
        else:
            sentence = "Was unable to close all files"

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
        if coming_intent == 'files_user_is_using':
            self.files_user_is_using(hermes, intent_message)
        if coming_intent == 'disconnect_current_user':
            self.disconnect_current_user(hermes, intent_message)
        if coming_intent == 'close_current_databases':
            self.close_current_databases(hermes, intent_message)





        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            #h.subscribe_intents(self.master_intent_callback).start()
	    h.subscribe_intent("multip:connect_to_server", self.master_intent_callback).start()

if __name__ == "__main__":
    snips_fmadmin()
