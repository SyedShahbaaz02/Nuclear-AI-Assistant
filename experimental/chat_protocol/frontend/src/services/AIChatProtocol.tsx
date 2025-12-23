import {
    AIChatMessage,
    AIChatProtocolClient,
    AIChatError,
} from "@microsoft/ai-chat-protocol";
import { MessageProps } from '../components/Message';
import { LogEntryProps } from '../components/LogEntry'

const initialAiMessage = { content: '...', role: 'assistant', sender: 'ai' } as MessageProps

function getLogEntry(message: string, logLevel: string = 'info'): LogEntryProps {
    return {
        timestamp: new Date().toISOString(),
        logLevel,
        source: 'AIChatProtocol',
        message
    }
}

function isChatError(entry: unknown): entry is AIChatError {
    return (entry as AIChatError).code !== undefined;
}

interface UpdateDisplayDelegates {
    updateStreamingMessage: (message: MessageProps, logEntry: LogEntryProps) => void,
    addStreamingMessage(message: MessageProps): void,
    addNonStreamingMessage(message: MessageProps, logEntry: LogEntryProps): void,
    logEntry(logEntry: LogEntryProps, streaming: boolean, func: boolean): void
}

export class AIChatProtocol {
    private client: AIChatProtocolClient;
    private function_client: AIChatProtocolClient;

    constructor() {
        this.client = new AIChatProtocolClient("http://localhost:3001/api/chat/");
        this.function_client = new AIChatProtocolClient("http://localhost:7071/api/chat/");
    }

    async sendMessage(
        message: MessageProps,
        messages: MessageProps[],
        delegates: UpdateDisplayDelegates,
        streaming: boolean,
        func: boolean = false): Promise<void> {
        try {
            const startTime = new Date().getTime();
            let sessionState = undefined;
            const allMessages = [...messages, message];
            const chatMessages = allMessages.map((messageProp) => {
                return {
                    content: messageProp.content,
                    role: messageProp.role
                } as AIChatMessage
            });

            if (streaming) {
                delegates.updateStreamingMessage(initialAiMessage,
                    getLogEntry('Sending messages to streaming service using AI Chat Protocol'));

                let result
                if (!func)
                    result = await this.client.getStreamedCompletion(chatMessages, {
                        sessionState
                    });
                else
                    result = await this.function_client.getStreamedCompletion(chatMessages, {
                        requestOptions: {
                            allowInsecureConnection: true
                        },
                        sessionState
                    });

                const latestMessage: MessageProps = { ...initialAiMessage, content: '' };
                for await (const response of result) {
                    if (!response.delta) {
                        continue;
                    }
                    if (response.sessionState) {
                        sessionState = response.sessionState;
                    }
                    if (response.delta.role) {
                        latestMessage.role = response.delta.role;
                    }
                    if (response.delta.content) {
                        latestMessage.content += response.delta.content;
                        delegates.updateStreamingMessage({ ...latestMessage },
                            getLogEntry('Received a chunk from the streaming service using AI Chat Protocol'));
                    }
                }
                delegates.updateStreamingMessage({ ...initialAiMessage, content: '' },
                    getLogEntry('End of streaming chat response'));
                delegates.addStreamingMessage(latestMessage);
                const endTime = new Date().getTime();
                const duration = endTime - startTime;
                delegates.logEntry(getLogEntry(`Streaming chat response took ${duration}ms`), streaming, func);
            } else {
                delegates.addNonStreamingMessage(initialAiMessage,
                    getLogEntry('Sending messages to non streaming service using AI Chat Protocol'));

                const result = await this.client.getCompletion(chatMessages, {
                    sessionState
                });
                const message = { ...initialAiMessage, content: result.message.content }
                delegates.addNonStreamingMessage(message,
                    getLogEntry('Received the message from the non streaming service using AI Chat Protocol'));
                const endTime = new Date().getTime();
                const duration = endTime - startTime;
                delegates.logEntry(getLogEntry(`Non streaming chat response took ${duration}ms`), streaming, false);
            }
        } catch (e) {
            if (isChatError(e)) {
                delegates.logEntry(getLogEntry(e.message, 'error'), streaming, func);
            }
        }
    }
}
