import httplib
import ssl
import json
import time




### ----------------------- CONSTANTS -------------------------- ###
TOKEN_TIMEOUT = 15 * 60         #time before token expires in seconds
REQUEST_TIMEOUT = 5             #requests timeout in seconds







class pyfmadmin:

	### --------------- CONSTRUCTOR / DECONSTRUCTOR  --------------- ###
	
	def __init__(self, hostname, username, password):
		self.baseurl = "/fmi/admin/api/v1"
		self.hostname = hostname
		self.username = username
		self.password = password
		self.timeOfLastCall = 0.0
		#self.login()
		
		
		
		
	#def __del__(self):
		#self.logout()
		

	
	
	
	
	
	
	
	
	
	
	### ------------------------ CONNECTION ----------------------- ###
	
	
	def httpsRequest (self, method, url, body, headers):
		ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
		self.conn = httplib.HTTPSConnection(self.hostname, timeout=REQUEST_TIMEOUT)
		self.conn._context = ctx
		self.conn.request(method, url, body, headers)
		responseDict = {}
		
		response = self.conn.getresponse()
		#print (response.status, response.reason)
		
		if response.status == httplib.OK:
			responseDict = json.loads(response.read())
			if responseDict["result"] == 0:
				self.timeOfLastCall = time.time()
		else:
			responseDict["result"] = -1
			responseDict["description"] = str(response.status) + ", " + response.reason	
		
		return responseDict	
		
		
		
	
	def login (self):
		url = self.baseurl + "/user/login"
		method = "POST"
		jsonBody = {"username": self.username, "password": self.password}
		body = json.dumps(jsonBody)
		headers = {"Content-Type": "application/json"}
				
		responseDict = self.httpsRequest(method, url, body, headers)
		
		if responseDict["result"] == 0:
			self.token = responseDict["token"]
			self.timeOfLastCall = time.time()
		
		return responseDict

	
	


	
	def logout (self):
		url = self.baseurl + "/user/logout"
		method = "POST"
		headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.token}
		body = ""
		
		responseDict = self.httpsRequest(method, url, body, headers)
				

		if responseDict["result"] == 0:
			self.token = ""	
			self.timeOfLastCall = 0.0
		
		self.conn.close()
		return responseDict
		





	def timeoutReconnect (self):
		if (time.time() - self.timeOfLastCall) > TOKEN_TIMEOUT:
			self.login()

	
	
	
	
	
	
	
	

	### ------------------------ DATABASES ------------------------ ###
	
	def list_databases (self):
		self.timeoutReconnect()
		
		url = self.baseurl + "/databases"
		method = "GET"
		headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.token}
		body = ""
		responseDict = {}
	
		responseDict = self.httpsRequest(method, url, body, headers)			

		return responseDict	

	
	
	def close_database (self, database_id, message=None):
		self.timeoutReconnect()
	
		url = self.baseurl + "/databases/" + str(database_id) + "/close"
		method = "PUT"
		headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.token}
		jsonBody = {}
		if message != None:
			jsonBody["message"] = str(message)
		body = json.dumps(jsonBody)		
		responseDict = {}
	
		responseDict = self.httpsRequest(method, url, body, headers)	
			
		return responseDict		
	



	def open_database (self, database_id, key=None):
		self.timeoutReconnect()
	
		url = self.baseurl + "/databases/" + str(database_id) + "/open"
		method = "PUT"
		headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.token}
		jsonBody = {}
		if key != None:
			jsonBody["message"] = str(key)
		body = json.dumps(jsonBody)		
		responseDict = {}
	
		responseDict = self.httpsRequest(method, url, body, headers)	
			
		return responseDict		
	
	
	
	### ------------------------- CLIENTS ------------------------- ###
	
	def send_message_to_client (self, client_id, message):
		self.timeoutReconnect()
	
		url = self.baseurl + "/clients/" + str(client_id) + "/message"
		method = "POST"
		headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.token}
		jsonBody = {"message": message}
		body = json.dumps(jsonBody)		
		responseDict = {}
	
		responseDict = self.httpsRequest(method, url, body, headers)	
			
		return responseDict	
	
	

	
	def send_message_to_clients (self, clientDict, message):
		self.timeoutReconnect()
		
		errorCount = 0
		
		for client in clientDict:
			url = self.baseurl + "/clients/" + str(client["id"]) + "/message"
			method = "POST"
			headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.token}
			jsonBody = {"message": message}
			body = json.dumps(jsonBody)		
	
			responseDict = self.httpsRequest(method, url, body, headers)	
	
			if responseDict["result"] != 0:
				errorCount = errorCount + 1

				
		return errorCount
	




	def disconnect_client (self, client_id, message=None, gracetime=None):
		self.timeoutReconnect()
	
		url = self.baseurl + "/clients/" + str(client_id) + "/disconnect"
		method = "PUT"
		headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.token}
		jsonBody = {}
		if message != None:
			jsonBody["message"] = str(message)
		if gracetime != None:
			jsonBody["gracetime"] = int(gracetime)
		body = json.dumps(jsonBody)		
		responseDict = {}
	
		responseDict = self.httpsRequest(method, url, body, headers)	
			
		return responseDict	
	
	
	
	
	