import React from 'react';
import './LogEntry.css';

interface LogEntryProps {
    timestamp: string;
    logLevel: string;
    source: string;
    message: string;
}

const LogEntry: React.FC<LogEntryProps> = ({ timestamp, logLevel, source, message }) => {
    return (
        <div className={`log-entry-container ${logLevel}`}>
            {timestamp}: {logLevel} {source} {message}
        </div >
    );
};

export { LogEntry };
export type { LogEntryProps };
