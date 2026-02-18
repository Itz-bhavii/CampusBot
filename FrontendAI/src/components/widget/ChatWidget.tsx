import { useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';
import { Bot, User, Send, Paperclip, LogOut, RotateCcw, Check, AlertCircle, Loader2 } from 'lucide-react';
import { useState } from 'react';
import api from '../../lib/api';

const Typewriter = ({ text, onUpdate }: { text: string; onUpdate?: () => void }) => {
    const [displayedText, setDisplayedText] = useState('');


    useEffect(() => {
        let index = 0;
        // setDisplayedText(''); 

        const interval = setInterval(() => {
            // Using index + 1 because slice end is exclusive
            if (index < text.length) {
                setDisplayedText(text.slice(0, index + 1));
                index++;
                onUpdate?.();
            } else {
                clearInterval(interval);
            }
        }, 20);

        return () => clearInterval(interval);
    }, [text]);

    return <p className="whitespace-pre-wrap break-words leading-relaxed">{displayedText}</p>;
};

const ChatWidget = () => {
    const { messages, sendMessage, isLoading, resetChat } = useChat();
    const { logout } = useAuth();
    const [input, setInput] = useState('');
    const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !isLoading) {
            sendMessage(input);
            setInput('');
        }
    };

    const handleLogout = () => {
        logout();
        // Don't close widget, just let it show login form
    };


    const handleFileUpload = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.pdf,.doc,.docx,.txt';
        input.onchange = async (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) {
                setUploadStatus('uploading');
                const formData = new FormData();
                formData.append('file', file);


                try {
                    // Let axios set the Content-Type header with the boundary automatically
                    // Need to explicitly remove the 'Content-Type': 'application/json' 
                    // set in the default axios instance, otherwise backend sees JSON instead of multipart.
                    const response = await api.post('/ingest', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                        }
                    });

                    if (response.status === 200 || response.status === 201 || response.status === 202) {
                        setUploadStatus('success');
                        setToast({ message: 'Document uploaded successfully', type: 'success' });
                        setTimeout(() => {
                            setUploadStatus('idle');
                            setToast(null);
                        }, 3000);
                    } else {
                        setUploadStatus('error');
                        setToast({ message: 'Failed to upload document', type: 'error' });
                        setTimeout(() => {
                            setUploadStatus('idle');
                            setToast(null);
                        }, 3000);
                    }
                } catch (error) {
                    console.error('Upload failed:', error);
                    setUploadStatus('error');
                    setToast({ message: 'Error uploading document', type: 'error' });
                    setTimeout(() => {
                        setUploadStatus('idle');
                        setToast(null);
                    }, 3000);
                }
            }
        };
        input.click();
    };

    return (
        <div className="h-full flex flex-col bg-slate-50 relative">
            <div className="bg-white border-b border-slate-200 px-3 py-2 flex items-center justify-end gap-2">
                <button
                    onClick={resetChat}
                    className="text-xs text-slate-600 hover:text-blue-600 flex items-center gap-1 px-2 py-1 hover:bg-slate-100 rounded transition-colors"
                    title="New chat"
                >
                    <RotateCcw className="w-3 h-3" />
                    <span>New</span>
                </button>
                <button
                    onClick={handleLogout}
                    className="text-xs text-red-600 hover:text-red-700 flex items-center gap-1 px-2 py-1 hover:bg-red-50 rounded transition-colors"
                    title="Logout"
                >
                    <LogOut className="w-3 h-3" />
                    <span>Logout</span>
                </button>
            </div>

            {/* Toast Notification */}
            {toast && (
                <div className={`absolute top-14 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-lg shadow-lg text-sm font-medium z-10 transition-all duration-300 ${toast.type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-red-100 text-red-800 border border-red-200'
                    }`}>
                    <div className="flex items-center gap-2">
                        {toast.type === 'success' ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                        <span>{toast.message}</span>
                    </div>
                </div>
            )}


            <div className={`flex-1 overflow-y-auto px-3 py-4 space-y-3 ${messages.length > 0 ? 'scrollbar-hide' : ''}`}>

                <style>{`
                    .scrollbar-hide::-webkit-scrollbar {
                        display: none;
                    }
                    .scrollbar-hide {
                        -ms-overflow-style: none;
                        scrollbar-width: none;
                    }
                `}</style>

                {messages.length === 0 ? (
                    <div className="flex flex-col gap-4">

                        {/* Welcome Messages */}
                        <div className="flex flex-col items-center justify-center h-64 text-center px-6">
                            <div className="w-16 h-16 bg-[#90243C] rounded-2xl flex items-center justify-center mb-4 shadow-lg rotate-3 transition-transform hover:rotate-0">
                                <Bot className="w-8 h-8 text-white" />
                            </div>
                            <h3 className="text-lg font-bold text-slate-900 mb-2">Hello! I'm CampusBot</h3>
                            <p className="text-sm text-slate-600 mb-6 max-w-[250px]">
                                I'm your AI assistant. Ask me anything about college admissions, programs, placements, or specific document queries.
                            </p>
                        </div>

                    </div>

                ) : (
                    messages.map((msg, index) => (
                        <div
                            key={msg.id}
                            className={`flex gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                        >

                            <div
                                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm ${msg.sender === 'bot' ? 'bg-[#90243C]' : 'bg-slate-700'
                                    }`}
                            >
                                {msg.sender === 'bot' ? (
                                    <Bot className="w-4 h-4 text-white" />
                                ) : (
                                    <User className="w-4 h-4 text-white" />
                                )}
                            </div>

                            <div
                                className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm shadow-sm overflow-hidden ${msg.sender === 'user'
                                    ? 'bg-blue-600 text-white rounded-tr-none'
                                    : 'bg-white text-slate-800 border border-slate-100 rounded-tl-none'
                                    }`}
                            >
                                {msg.sender === 'bot' && index === messages.length - 1 ? (
                                    <Typewriter text={msg.text} onUpdate={scrollToBottom} />
                                ) : (
                                    <p className="whitespace-pre-wrap break-words leading-relaxed">{msg.text}</p>
                                )}
                            </div>
                        </div>
                    ))
                )}


                {isLoading && (
                    <div className="flex gap-2">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm bg-[#90243C]">
                            <Bot className="w-4 h-4 text-white" />
                        </div>
                        <div className="flex items-center gap-1 px-4 py-4 bg-white border border-slate-100 rounded-2xl rounded-tl-none shadow-sm h-[46px]">
                            <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <div className="bg-white border-t border-slate-200 p-3">
                <form onSubmit={handleSubmit} className="flex items-end gap-2">
                    <button
                        type="button"
                        onClick={handleFileUpload}
                        disabled={uploadStatus !== 'idle'}
                        className={`p-2 rounded-lg transition-colors flex-shrink-0 ${uploadStatus === 'error' ? 'text-red-500 hover:bg-red-50' :
                            uploadStatus === 'success' ? 'text-green-500 hover:bg-green-50' :
                                'text-slate-500 hover:text-blue-600 hover:bg-blue-50'
                            }`}
                        title="Upload document"
                    >
                        {uploadStatus === 'uploading' && <Loader2 className="w-4 h-4 animate-spin" />}
                        {uploadStatus === 'success' && <Check className="w-4 h-4" />}
                        {uploadStatus === 'error' && <AlertCircle className="w-4 h-4" />}
                        {uploadStatus === 'idle' && <Paperclip className="w-4 h-4" />}
                    </button>

                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                        placeholder="Ask a question..."
                        disabled={isLoading}
                        rows={1}
                        className="flex-1 bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none max-h-24"
                        style={{ minHeight: '36px' }}
                    />

                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
                        title="Send"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatWidget;