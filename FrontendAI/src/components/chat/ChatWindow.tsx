import { useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import MessageBubble from './MessageBubble';
import InputArea from './InputArea';
import { BookOpen } from 'lucide-react';

const ChatWindow = () => {
    const { messages, sendMessage, isLoading } = useChat();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    return (
        <div className="flex flex-col h-full bg-white">
            <div className="flex-1 overflow-y-auto px-4 py-6">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-2xl mx-auto">
                        <div className="bg-blue-100 p-6 rounded-2xl mb-6">
                            <BookOpen className="w-12 h-12 text-blue-600 mx-auto" />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-900 mb-3">
                            Welcome to Campus Knowledge Assistant
                        </h2>
                        <p className="text-slate-600 mb-6 max-w-lg">
                            Ask questions about campus policies, regulations, schedules, or upload your own documents for personalized assistance.
                        </p>
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-slate-700">
                            <p className="font-medium mb-2">You can ask about:</p>
                            <ul className="text-left space-y-1 text-slate-600">
                                <li>• Campus rules and regulations</li>
                                <li>• Academic schedules and deadlines</li>
                                <li>• Course information and requirements</li>
                                <li>• Or upload documents for analysis</li>
                            </ul>
                        </div>
                    </div>
                ) : (
                    <div className="max-w-4xl mx-auto w-full">
                        {messages.map((msg, index) => (
                            <MessageBubble
                                key={msg.id}
                                message={msg}
                                isLast={index === messages.length - 1}
                            />
                        ))}
                        {isLoading && (
                            <div className="flex justify-start mb-6">
                                <div className="flex items-center gap-2 px-4 py-3 bg-slate-100 rounded-2xl text-slate-600 text-sm">
                                    <div className="flex gap-1">
                                        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                    <span>Thinking...</span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            <div className="border-t border-slate-200 bg-white p-4">
                <div className="max-w-4xl mx-auto">
                    <InputArea onSend={sendMessage} disabled={isLoading} />
                </div>
            </div>
        </div>
    );
};

export default ChatWindow;
