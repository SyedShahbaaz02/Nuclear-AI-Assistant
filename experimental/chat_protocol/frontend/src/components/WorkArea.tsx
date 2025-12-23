import ChatContainer, { ChatType } from './ChatContainer';
import { RootState } from '../store';
import { useSelector } from 'react-redux';
import './WorkArea.css';
import UserInput from './UserInput';

const WorkArea = () => {
  const streamingWAIChatMessages = useSelector((state: RootState) => state.streamingMessages);
  const streamingWAIChatLog = useSelector((state: RootState) => state.streamingLog);
  const nonStreamingMessages = useSelector((state: RootState) => state.nonStreamingMessages);
  const nonStreamingLog = useSelector((state: RootState) => state.nonStreamingLog);
  const streamingFunctionMessages = useSelector((state: RootState) => state.streamingFunctionMessages);
  const streamingFunctionLog = useSelector((state: RootState) => state.streamingFunctionLog);

  return (
    <>
      <div className="work-area">
        <ChatContainer
          chatType={ChatType.NonStreaming}
          messages={nonStreamingMessages}
          logEntries={nonStreamingLog} />
        <ChatContainer
          chatType={ChatType.AIChatStreaming}
          messages={streamingWAIChatMessages}
          logEntries={streamingWAIChatLog} />
        <ChatContainer
          chatType={ChatType.FunctionStreaming}
          messages={streamingFunctionMessages}
          logEntries={streamingFunctionLog} />
      </div>
      <UserInput />
    </>
  );
};

export default WorkArea;