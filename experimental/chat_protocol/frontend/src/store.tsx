import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { MessageProps } from './components/Message';
import { LogEntryProps } from './components/LogEntry';

const initialMessages: MessageProps[] = [];
const initialLogEntries: LogEntryProps[] = [];

const streamingMessagesSlice = createSlice({
  name: 'streamingMessages',
  initialState: initialMessages,
  reducers: {
    addStreamingMessage: (state, action: PayloadAction<MessageProps>) => {
      state.push(action.payload);
    },
    setStreamingMessage: (state, action: PayloadAction<MessageProps>) => {
      const lastMessage = state.pop();
      // Only want to pop non user related messages
      if (lastMessage?.role === 'user') {
        state.push(lastMessage);
      }
      state.push(action.payload);
    }
  }
});

const streamingLogSlice = createSlice({
  name: 'streamingLog',
  initialState: initialLogEntries,
  reducers: {
    addStreamingLogEntry: (state, action: PayloadAction<LogEntryProps>) => {
      state.push(action.payload);
    }
  }
});

const streamingFunctionMessagesSlice = createSlice({
  name: 'streamingFunctionMessages',
  initialState: initialMessages,
  reducers: {
    addStreamingFunctionMessage: (state, action: PayloadAction<MessageProps>) => {
      state.push(action.payload);
    },
    setStreamingFunctionMessage: (state, action: PayloadAction<MessageProps>) => {
      const lastMessage = state.pop();
      // Only want to pop non user related messages
      if (lastMessage?.role === 'user') {
        state.push(lastMessage);
      }
      state.push(action.payload);
    }
  }
});

const streamingFunctionLogSlice = createSlice({
  name: 'streamingFunctionLog',
  initialState: initialLogEntries,
  reducers: {
    addStreamingFunctionLogEntry: (state, action: PayloadAction<LogEntryProps>) => {
      state.push(action.payload);
    }
  }
});

const nonStreamingMessagesSlice = createSlice({
  name: 'nonStreamingMessages',
  initialState: initialMessages,
  reducers: {
    addNonStreamingMessage: (state, action: PayloadAction<MessageProps>) => {
      if (state[state.length - 1]?.content == '...') {
        state.pop();
      }
      state.push(action.payload);
    }
  }
});

const nonStreamingLogSlice = createSlice({
  name: 'nonStreamingLog',
  initialState: initialLogEntries,
  reducers: {
    addNonStreamingLogEntry: (state, action: PayloadAction<LogEntryProps>) => {
      state.push(action.payload);
    }
  }
});

const store = configureStore({
  reducer: {
    streamingMessages: streamingMessagesSlice.reducer,
    nonStreamingMessages: nonStreamingMessagesSlice.reducer,
    streamingLog: streamingLogSlice.reducer,
    nonStreamingLog: nonStreamingLogSlice.reducer,
    streamingFunctionMessages: streamingFunctionMessagesSlice.reducer,
    streamingFunctionLog: streamingFunctionLogSlice.reducer
  }
});

export const { addStreamingMessage, setStreamingMessage } = streamingMessagesSlice.actions;
export const { addStreamingFunctionMessage, setStreamingFunctionMessage } = streamingFunctionMessagesSlice.actions;
export const { addStreamingFunctionLogEntry } = streamingFunctionLogSlice.actions;
export const { addNonStreamingMessage } = nonStreamingMessagesSlice.actions;
export const { addStreamingLogEntry } = streamingLogSlice.actions;
export const { addNonStreamingLogEntry } = nonStreamingLogSlice.actions;
export type RootState = ReturnType<typeof store.getState>;
export default store;
