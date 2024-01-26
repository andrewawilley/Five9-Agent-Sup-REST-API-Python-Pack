### README Status:
This Readme is somewhat under construction.  If you identify incorrect or missing information, please submit a pull request or open an issue.

# Overview

The Five9 Agent-Sup REST API Python Pack provides an example interface for interacting with Agent and Supervisor sessions in the Five9 Virtual Contact Center (VCC). It simplifies the process of integrating Five9's REST APIs into your Python applications, enabling you to perform agent and supervisor REST API methods, as well as open websockets for real-time interaction and notifications.


# DISCLAIMER
This repository contains sample code which is **not an official Five9 resource**. It's intended for educational and illustrative purposes only, demonstrating potential ways to utilize APIs in the Five9 contact center environment.

By choosing to use this code, you acknowledge and agree to the following:

- This is **not** officially endorsed or supported software by Five9.
- All customizations, modifications, or deployments made with this code are entirely at your **own risk** and **responsibility**. 
- The provided code may not cover all possible use cases and may not apply to your specific needs without further modification.
- Five9 will **not** provide any support or assume any liability for any issues that may arise from the use of this code.


# Features
* Session Management: Handle login sessions, manage session metadata, and ensure proper authentication for API calls.
* Agent Operations: Perform actions related to Five9 agents, including session management and handling maintenance notices.
* Supervisor Operations: Manage supervisor sessions and perform tasks such as starting sessions, accepting maintenance notices, and logging out.
* WebSocket Support: Establish WebSocket connections for real-time interaction and notifications, with built-in event handling and message processing.


# Getting Started
## Prerequisites
* Tested Python 3.12 or higher, though it should work with Python 3.11 as well
* Five9 Virtual Contact Center (VCC) account with the Agent or Supervisor Role as appropriate for your use case

## Installation
Clone the repository to your local machine, create a virtual environment, and install using pip.

### Windows
```powershell
git clone <insert URL from GIT here>
cd five9-python-pack
python -m venv venv
.\venv\Scripts\activate
pip install .
```
### Linux/MacOS
```bash
git clone <insert URL from GIT here>
cd five9-python-pack
python -m venv venv
source venv/bin/activate
pip install .
```

Note, if you need to customize the package, you can install it in editable mode by running `pip install -e .` instead of `pip install .`

# Configuration
Before you start using the libaray, ensure that the `config.py` file is updated to the correct local if you are connecting to a non-US call center environment.

## Credentials
For testing purposes, you can create a credentials.py file in the private folder with the following content:

```python
# credentials.py
ACCOUNTS = {
    'default_test_account': {
        'username': 'anActiveUser@your_call_center',
        'password': 'supersecretpassword',
    }
}
```
This will allow you to run the tests without having to enter your credentials every time.  **DO NOT** commit this file to the repository, and consider using a different method of storing credentials for production use such as environment variables.


# REST Client Usage
## Initializing the Client
To initialize the client, first import the `Five9Client` class from the `five9.client` module.  Then, you can create a new instance of the client by passing in the account credentials:

```python
from five9.client import Five9RestClient

# if you have a credentials.py file in the private folder, you can import the credentials from there
from five9.private.credentials import ACCOUNTS

username = ACCOUNTS["default_test_account"]["username"]
password = ACCOUNTS["default_test_account"]["password"]

client = Five9RestClient(username='your_username', password='your_password')
```

### Starting an Agent or Supervisor Session
Once the client has been instantiated, you can start an agent or supervisor session by calling the `initialize_agent_session()` or `initialize_supervisor_session()` methods, respectively.  These methods will return a boolean value indicating whether the session was successfully started.

```python
client.initialize_supervisor_session()
```

## Implementing Supervisor and Agent REST Methods
A number of the documented REST methods are implemented in the `supervisor` and `agent` modules, respectively.  To implement additional methods, you can create a new instance of the supervisor or agent class in the `methods.agent_methods` or `methods.supervisor_methods` modules, respectively.

There is a #TODO item to implement a method on the client that will allow you to pass in a list of method names to implement, but for now you must import the methods directly in the respective modules.

To implement a method documented in the developers guide, you can create a new class that inherits from the `AgentRestMethod` or `SupervisorRestMethod` class, depending on the type of method you are implementing.  The class must implement the `method_name` property, which should be the name of the method as documented in the developers guide.  

For example, follow this pattern
* Name the class after the method name, but with the first letter capitalized and the underscores removed.  For example, the `GET /orgs/{orgId}/skills` method would be named `DomainQueues`.
* The class must inherit from the `AgentRestMethod` or `SupervisorRestMethod` class, depending on the type of method you are implementing.
* Add a docstring to the class that contains the method description from the developers guide, as well as the method path.  This is not required, but it is helpful for documentation purposes.
* Implement the `invoke()` method.  This method should set the `method` and `path` properties, and then call the `super().invoke()` method.  This will invoke the method and store the response in the `response` property.  The `invoke()` method should, at a minimum, return the `response` object, but for many of the REST methods, you will want to pass the json value of the response.
    
```python
from five9client.methods.base import SupervisorRestMethod

class DomainQueues(SupervisorRestMethod):
    """Returns an array of all queues in the domain.
    GET /orgs/{orgId}/skills

    """

    def invoke(self):
        self.method = "GET"
        self.path = f"/orgs/{self.config.orgId}/skills"
        super().invoke()
        # return the json value of the response if the method has a response body that needs
        # to be processed by the calling method.
        return self.response.json()

```

## Invoking REST Methods
Once a session has been started, you can invoke REST methods by calling the `invoke()` method on the client method class instance.  Pass in the correct payload for the method you are calling, and the method will be invoked.  Though this can vary depending on the method, most methods will return a requests.response object.  You can access the response data by calling the `json()` method on the response object.


# Supervisor and Agent WebSocket Usage
## Starting the WebSocket
To start the WebSocket, you must first import the `Five9WebSocket` class from the `websocket` module.  Then, you can create a new instance of the WebSocket by passing in the client instance:

The socket will automatically connect to the Five9 WebSocket server.  It requires three arguments:
* `client`: The client instance to use for authentication and session management.
* `type`: The type of session to start.  Valid values are `agent` and `supervisor`.
* `socket_key`: This is an **arbitrary** string that is used to identify the socket.  Only one socket can be started per socket key.  If you attempt to start a socket with a key that is already in use, it will fail to connect.


```python
from five9client.websocket import Five9WebSocket

client = Five9RestClient(username=username, password=password)
client.initialize_supervisor_session()

supervisor_socket = Five9Socket(client, "supervisor", "demo_script")
supervisor_socket.connect()
```

## Defining a Message Handler
You can create subclasses objects of `SocketEventHandler` to handle incoming message events.  Pass them in as a list to the `Five9Client` with the `custom_socket_handlers` argument, and they will be used to handle incoming messages.

  The `handle_message(event)` method will be called when a message of the `eventId` is received.  The `event` argument will be the full message object from the websocket, and you can access the `context` and `payLoad` properties from the event object.

The complete list of message eventIds and their corresponding message types can be found in the [Five9 Agent and Supervisor REST API documentation](https://webapps.five9.com/assets/files/for_customers/documentation/apis/vcc-agent+supervisor-rest-api-reference-guide.pdf) in the last part of the document.  

In the example below, we create a new class called QueueSatistics to help track changes in the queue data.  We then create a new class called StatsEvent5000Handler that inherits from the `SocketEventHandler` class.  This class will handle the 5000 event, which is the Statistics Update event.  When the event is received, the `handle()` method will be called, and the `event` argument will contain the full event object.  We can then process the event as needed.

```python
from five9_agent_sup_rest.client import Five9RestClient, Five9Socket
from five9_agent_sup_rest.methods.default_socket_handlers import SocketEventHandler

class QueueStatistics:
    def __init__(self, *args, **kwargs):
        self.queue_id_map = {}
        self.queue_mapping_info = kwargs.get("queue_mapping_info", None)
        self.map_queue_ids()

        self.current_queue_snapshot = {
            "added": [],
            "updated": [],  
            "removed": [],
        }

    def map_queue_ids(self):
        for queue in self.queue_mapping_info:
            self.queue_id_map[queue["id"]] = queue["name"]

    def update_queue_info(self, queue_info):
        self.previous_queue_snapshot = self.current_queue_snapshot
        self.current_queue_snapshot = queue_info

class StatsEvent5000Handler(SocketEventHandler):
    """Handler for event 5000 - Statistics Update"""

    eventId = "5000"

    def __init__(self, *args, **kwargs):
        super().__init__(eventId=self.eventId, *args, **kwargs)
        if not hasattr(self.client, "queue_statistics"):
            self.client.queue_statistics = QueueStatistics(
                queue_mapping_info=self.client.supervisor.DomainQueues.invoke()
            )
            logging.info("Queue Statistics Handler Initialized")

    async def handle(self, event):
        logging.info(
            f"Stats Handler EVENT: {event['context']['eventId']} - {event['payLoad']}"
        )
        for updated_object in event["payLoad"]:
            if updated_object["dataSource"] == "ACD_STATUS":
                self.client.queue_statistics.update_queue_info(updated_object["data"])

        return
```
