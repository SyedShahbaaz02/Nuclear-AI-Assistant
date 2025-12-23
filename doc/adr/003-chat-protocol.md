# Streaming vs Non-Streaming and API Chat Protocol vs SignalR

This ADR explores 2 overarching questions.

* Should we design the backend/frontend communications to account for streaming the output of an LLM call?
* Should we use the API Chat Protocol or SignalR to accomplish the communication between the frontend and backend?

This ADR did have some experimentation work done to explore these questions. That work can be found at
[Chat Protocol Experiments](../../experimental/chat_protocol/).

## Status

In Progress

## Context

It has been seen in past Chat engagements, that retrofitting streaming chat capabilities into a solution, that wasn't
designed to accomidate it, is often a great enough of a challenge that the limited situations where it would have
value often don't justify the effort. This effort is driven from a combination of micro design decisions within the
backend and frontend application code structure, and with larger architectural decisions related to the layers that
exist between the frontend and backend.

## Options

* Non streaming HTTP Post
* Streaming using HTTP Streaming Protocol
  * With Microsoft API Chat Protocol
  * Without Microsoft API Chat Protocol
  * Hosting Platform
    * Function Apps: depends on [HTTP Streams preview feature](https://techcommunity.microsoft.com/blog/azurecompute/azure-functions-support-for-http-streams-in-python-is-now-in-preview/4146697)
    * App Services
    * Azure Container Apps
* Streaming using Websockets aka SignalR
  * Python Azure Functions
  * C#
    * Azure Functions
    * ASP.Net

## To Stream or Not to Stream

The primary value of streaming is related to the perceived response time to the end user, aka how quickly does the user
start to see a response from their inquiry. In tests done using the structure created in the experimental section of
this repo, it was observed that small responses (2 or less paragraphs) had nearly identical, percieved, response times.
The actual full response times actually favored the streaming response (not something I expected).
When responses were larger the benifits of the streamed response were more noticible. Streaming also continued to have
better full response times than the Non Streaming responses.

With that exploration we favor a decision to stream the response.

## Websockets aka SignalR vs HTTP Streaming Response

Now that we know were going to stream the response we need to decide how. There are two major options that each have
their own branches of decisions to make. They are to Stream using Websockets or Stream using HTTP Streaming response.
Let's break each down just a little.

### Websocket aka SignalR

The greatest benefit of using Websockets is the ability to maintain a durable 2 way communication between the Client
and the Server. One that isn't limited to the scope of a single Http POST request, but instead stays open to allow for
continued communication both ways. This option really shines when we think of the ability to have a collaborative chat
experience.

With the bi-directional communication capabilities of a Web Socket, the server serves as mediator between the different
clients. So when User A sends a message to the conversation, the server can relay that messages to all other connected
users of the conversation.

For streaming purposes the User would post a message to the server, a background worker would recieve that message and
communicate with the LLM. The response from the LLM would then be streamed back to all users connected to the
conversation through the WebSocket connection.

The structure of what this would look like is:

![Streaming SignalR Diagram](/doc/assets/chat_protocol/websocket-streaming.drawio.png)

It's important to note that there is a greater level of complexity in a collaboration chat then just how we ensure all
users are receiving updates in real time from the conversation. To name a few:

* How do we know a message from a user is intended for the LLM to respond versus another user?
* What happens when a multiple users send a message intended for the LLM?
* What happens when user try to interupt an LLMs response?

This particular approach is a fairly heavy handed if we are only dealing with a single user chat experience.

Other things to consider with SignalR, Python doesn't have a large community that uses SignalR. So samples of using
it are light. C# is where SignalR was born and therefore has the greatest amount of samples/examples and community
support associated within it.

### HTTP Streaming Response

An HTTP Streaming response approach is the simplier of the 2 options. It is essentially a HTTP POST request that keeps
the connection open to the client for the Server to stream response back until either the server completes it request
or the client abondons the connection. The connection are much shorter lived and are unidirectional.

The diagram for this kind of structure would like this:

![HTTP Streaming Response Diagram](/doc/assets/chat_protocol/http-streaming-response.drawio.png)

The complexity with this approach is much lower.

This approach has a couple of risks associated with it.

When used with an Azure Function, we are dependant on preview functionality namely this:
[HTTP Stream with Python Azure Functions](https://techcommunity.microsoft.com/blog/azurecompute/azure-functions-support-for-http-streams-in-python-is-now-in-preview/4146697)
This feature is targeted to be GA prior to the end of our engagement scope, so the risk is limited to the PG meeting
that expectation.
The second risk is with the use of Azure Functions itself, and their transient nature. To be successful the connection
between the Client and the Function most be maintained for the duration of the streamed response. If the Function app
instance is torn down while a response is being streamed a completely new connection would be created with a completely
different LLM streaming response. This is risk would be seen when the system is at scale. Our engagements use case
shouldn't have scaling demand that would create this scenario.

An alternative would be to use an Azure Web App or an Azure Container App to host the backend and that would reduce
both of the risks. The overall solution doesn't have a high enough level of complexity to warrent an Azure Container
App, so advice Azure Web Application over an Azure Container App if we choose to mitigate this risk by not using
Azure Functions.

## Decision

The decision for this engagement is to move forward with Streaming the responses using the Microsoft API Chat
Protocol, hosting on Azure Function Apps using the HTTP Streams with Python trigger binding. The endpoints on the
functions should be very light on logic to enable porting to an Azure Web Application in the event that we see issues
with the Azure Function when at scale.

## Consequences

By using the Http Streaming Approach, we're saying the collaborative experience is off the table for the scope of this
engagement. While the system can always be retrofitted with a SignalR archtitecture at a later date, we won't be making
architectural decisions now to keep that on the table.

The use of the Microsoft API Chat Protocol has a very low level of impact as the package itself is fairly light
weight in functionality.

The use of Azure Function Apps for the backend puts the dependance on a feature that, at the time of writing
this ADR, is not yet GA'd. This puts a risk that we may need to pivot to using Azure Web Applications for the backend,
a risk that can be easily migigated through SOLID design preciples being applied and seperating the hosting
responsibility from the logic of the backend.
