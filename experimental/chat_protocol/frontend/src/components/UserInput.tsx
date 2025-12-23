import React, { Dispatch, useState } from 'react';
import './UserInput.css';
import { MessageProps } from './Message';
import { useDispatch, useSelector } from 'react-redux';
import {
  addStreamingMessage, addNonStreamingMessage, addNonStreamingLogEntry, addStreamingLogEntry,
  RootState, setStreamingMessage, addStreamingFunctionLogEntry, addStreamingFunctionMessage,
  setStreamingFunctionMessage
} from '../store';
import { AIChatProtocol } from '../services/AIChatProtocol';
import { UnknownAction } from '@reduxjs/toolkit';
import { LogEntryProps } from './LogEntry';

const UserInput: React.FC = () => {
  const [input, setInput] = useState<string>('');
  const dispatch = useDispatch();
  const streamingMessages = useSelector((state: RootState) => state.streamingMessages);
  const streamingFunctionMessages = useSelector((state: RootState) => state.streamingFunctionMessages);
  const nonStreamingMessages = useSelector((state: RootState) => state.nonStreamingMessages);
  const aiChatProtocolClient = new AIChatProtocol();

  const dispatchUpdates = (dispatch: Dispatch<UnknownAction>, message: MessageProps) => {
    const logEntry = {
      timestamp: new Date().toISOString(),
      logLevel: 'info',
      source: 'UserInput',
      message: 'User message entered'
    };
    dispatch(addStreamingMessage(message));
    dispatch(addStreamingLogEntry(logEntry));
    dispatch(addStreamingFunctionMessage(message));
    dispatch(addStreamingFunctionLogEntry(logEntry));
    dispatch(addNonStreamingMessage(message));
    dispatch(addNonStreamingLogEntry(logEntry));
  }

  const dispatchUpdateStreamingMessage = (message: MessageProps, logEntry: LogEntryProps) => {
    dispatch(setStreamingMessage(message))
    dispatch(addStreamingLogEntry(logEntry));
  }

  const dispatchUpdateStreamingFunctionMessage = (message: MessageProps, logEntry: LogEntryProps) => {
    dispatch(setStreamingFunctionMessage(message))
    dispatch(addStreamingFunctionLogEntry(logEntry));
  }

  const dispatchAddStreamingMessage = (message: MessageProps) => {
    dispatch(addStreamingMessage(message))
  }

  const dispatchAddStreamingFunctionMessage = (message: MessageProps) => {
    dispatch(addStreamingFunctionMessage(message))
  }

  const dispatchAddNonStreamingMessage = (message: MessageProps, logEntry: LogEntryProps) => {
    dispatch(addNonStreamingMessage(message));
    dispatch(addNonStreamingLogEntry(logEntry));
  }

  const dispatchLogEntry = (logEntry: LogEntryProps, streaming: boolean, func: boolean) => {
    if (streaming) {
        if(!func)
            dispatch(addStreamingLogEntry(logEntry));
        else
            dispatch(addStreamingFunctionLogEntry(logEntry));
    } else {
      dispatch(addNonStreamingLogEntry(logEntry));
    }
  }

  const delegates = {
    updateStreamingMessage: dispatchUpdateStreamingMessage,
    addStreamingMessage: dispatchAddStreamingMessage,
    addNonStreamingMessage: dispatchAddNonStreamingMessage,
    logEntry: dispatchLogEntry
  };

  const function_delegates = {
    updateStreamingMessage: dispatchUpdateStreamingFunctionMessage,
    addStreamingMessage: dispatchAddStreamingFunctionMessage,
    addNonStreamingMessage: dispatchAddNonStreamingMessage,
    logEntry: dispatchLogEntry
  };

  const handleSendMessage = () => {
    if (input.trim()) {
      const message = {
        content: input, role: "user", sender: 'user'
      } as MessageProps;
      // Dispatch both actions when a message is added
      dispatchUpdates(dispatch, message);
      sendMessage(message, aiChatProtocolClient, delegates);
      setInput('');
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSendMessage();
    }
  };

  const sendMessage = async (message: MessageProps, aiChatProtocolClient: AIChatProtocol, delegates: any) => {
    await aiChatProtocolClient.sendMessage(message, nonStreamingMessages, delegates, false);
    await aiChatProtocolClient.sendMessage(message, streamingMessages, delegates, true);
    await aiChatProtocolClient.sendMessage(message, streamingFunctionMessages, function_delegates, true, true);
  }

  return (
    <div className="message-input">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyUp={handleKeyPress}
        placeholder="Type your message..."
      />
      <button onClick={handleSendMessage}>Send</button>
    </div>
  );
};

export default UserInput;
