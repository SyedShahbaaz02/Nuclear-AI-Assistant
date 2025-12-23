import React from 'react';
import ReactMarkdown from 'react-markdown';
import './Message.css';

interface MessageProps {
  content: string;
  role: string;
  sender: string
}

const Message: React.FC<MessageProps> = ({ content, sender }) => {
  const messageClass = content ? `message ${sender}` : 'message hidden';
  return (
    <div className={messageClass}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div >
  );
};

export { Message };
export type { MessageProps };