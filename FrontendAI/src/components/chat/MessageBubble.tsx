import { User, Bot } from 'lucide-react';
import Typewriter from './Typewriter';

interface Message {
    id: string;
    sender: 'user' | 'bot';
    text: string;
    timestamp: Date;
}

const MessageBubble = ({ message, isLast }: { message: Message; isLast: boolean }) => {
    const isUser = message.sender === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6 animate-slideIn`}>
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center mr-3 shadow-sm flex-shrink-0">
                    <Bot className="w-4 h-4 text-white" />
                </div>
            )}

            <div className={`max-w-[70%] ${isUser ? 'order-1' : 'order-2'}`}>
                <div
                    className={`px-4 py-3 rounded-2xl ${
                        isUser
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'bg-slate-100 text-slate-800 border border-slate-200'
                    }`}
                >
                    {isUser || !isLast ? (
                        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{message.text}</p>
                    ) : (
                        <Typewriter text={message.text} />
                    )}
                </div>
                <span className={`text-xs text-slate-500 mt-1 block ${isUser ? 'text-right' : 'text-left'}`}>
                    {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>

            {isUser && (
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center ml-3 shadow-sm flex-shrink-0">
                    <User className="w-4 h-4 text-white" />
                </div>
            )}

            <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-slideIn {
          animation: slideIn 0.3s ease-out;
        }
      `}</style>
        </div>
    );
};

export default MessageBubble;
