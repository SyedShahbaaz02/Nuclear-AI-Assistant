import './ChatContainer.css';
import { LogEntry, LogEntryProps } from './LogEntry';
import { Message, MessageProps } from './Message';


enum ChatType {
  AIChatStreaming,
  FunctionStreaming,
  NonStreaming
}

interface ChatContainerProps {
  chatType: ChatType;
  messages: MessageProps[];
  logEntries: LogEntryProps[];
}

const ChatContainer = ({ chatType, messages, logEntries }: ChatContainerProps) => {
  let title = '';
  switch (chatType) {
    case ChatType.AIChatStreaming:
      title = 'Streaming w/AI Chat Protocol';
      break;
    case ChatType.FunctionStreaming:
      title = 'Streaming w/Azure Function';
      break;
    case ChatType.NonStreaming:
      title = 'Non-Streaming w/AI Chat Protocol';
      break;
  }

  return (
    <div className="form-container">
      <div className="form-title">
        {title}
      </div>
      <div className="form-content">
        <div className="message-list">
          {messages.map((messageProps, index) => (
            <Message
              key={index}
              {...messageProps}
            />
          ))}
        </div>
        <div className="log">
          {logEntries.map((logEntry, index) => (
            <LogEntry
              key={index}
              {...logEntry}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;
export type { ChatContainerProps };
export { ChatType };