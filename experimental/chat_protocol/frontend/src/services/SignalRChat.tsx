import * as signalR from '@microsoft/signalr';
import { MessageProps } from '../components/Message';
import { LogEntryProps } from '../components/LogEntry';

const initialAiMessage = { content: '...', role: 'assistant', sender: 'ai' } as MessageProps;

function getLogEntry(message: string, logLevel: string = 'info'): LogEntryProps {
    return {
        timestamp: new Date().toISOString(),
        logLevel,
        source: 'SignalRChatService',
        message
    };
}

interface SignalRUpdateDisplayDelegates {
    updateStreamingMessage: (message: MessageProps, logEntry: LogEntryProps) => void,
    addStreamingMessage(message: MessageProps): void,
    logEntry(logEntry: LogEntryProps, streaming: boolean): void
}

export class SignalRChatService {
    private connection: signalR.HubConnection;
    private startTime: number = new Date().getTime();
    private latestMessage: MessageProps = { ...initialAiMessage, content: '' };
    private delegates: SignalRUpdateDisplayDelegates;

    constructor(hubUrl: string, delegates: SignalRUpdateDisplayDelegates) {
        this.delegates = delegates;
        this.connection = new signalR.HubConnectionBuilder()
            .withUrl(hubUrl)
            .withAutomaticReconnect()
            .configureLogging(signalR.LogLevel.Information)
            .withHubProtocol(new signalR.JsonHubProtocol())
            .build();

        this.connection.on('ReceiveMessage', (message: MessageProps) => {
            if (message.content !== 'END') {
                this.latestMessage.content += message.content;
                delegates.updateStreamingMessage({ ...this.latestMessage },
                    getLogEntry('Received a chunk from the streaming service using AI Chat Protocol'));
            } else {
                delegates.updateStreamingMessage({ ...initialAiMessage, content: '' },
                    getLogEntry('End of streaming chat response'));
                delegates.addStreamingMessage(this.latestMessage);
                const endTime = new Date().getTime();
                const duration = endTime - this.startTime;
                console.log(`SignalR message duration: ${duration}ms`);
                this.latestMessage = { ...initialAiMessage, content: '' };
            }
        });

        this.connection.start().catch(err => console.error('SignalR Connection Error:', err));
    }

    async sendMessage(
        message: MessageProps,
        messages: MessageProps[]
    ): Promise<void> {
        try {
            this.startTime = new Date().getTime();
            const allMessages = [...messages, message];
            const chatMessages = allMessages.map((messageProp) => {
                return {
                    content: messageProp.content,
                    role: messageProp.role
                };
            });

            this.delegates.updateStreamingMessage(initialAiMessage,
                getLogEntry('Sending messages to SignalR service'));

            const apiUrl = process.env.REACT_APP_SIGNALR_API_URL || '/api/chat/signalr';
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ messages: chatMessages })
            });

            if (!response.ok) {
                this.delegates.logEntry(getLogEntry(`Failed to send messages: ${response.statusText}`, 'error'), true);
                throw new Error(`Failed to send messages: ${response.statusText}`);
            }
        } catch (e) {
            this.delegates.logEntry(getLogEntry(`Error sending message via SignalR: ${e}`, 'error'), true);
        }
    }
}