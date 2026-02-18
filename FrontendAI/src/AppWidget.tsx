import { useState, useEffect } from 'react';
import { MessageCircle, X, Minus, Maximize2 } from 'lucide-react';
import { useAuth } from './context/AuthContext';
import { ChatProvider } from './context/ChatContext';
import LoginWidget from './components/widget/LoginWidget';
import ChatWidget from './components/widget/ChatWidget';

const WidgetContainer = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isMinimized, setIsMinimized] = useState(false);
    const [isAnimating, setIsAnimating] = useState(false);
    const { isAuthenticated } = useAuth();


    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.altKey && e.key === 'c') {
                toggleWidget();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isMinimized]);


    const toggleWidget = () => {
        setIsAnimating(true);
        if (isMinimized) {
            setIsMinimized(false);
        } else {
            setIsOpen(prev => !prev);
        }
        setTimeout(() => setIsAnimating(false), 300);
    };

    const closeWidget = () => {
        setIsAnimating(true);
        setIsOpen(false);
        setIsMinimized(false);
        setTimeout(() => setIsAnimating(false), 300);
    };

    const minimizeWidget = () => {
        setIsAnimating(true);
        setIsMinimized(true);
        setTimeout(() => setIsAnimating(false), 300);
    };

    const expandWidget = () => {
        setIsAnimating(true);
        setIsMinimized(false);
        setTimeout(() => setIsAnimating(false), 300);
    };

    return (
        <>
            {/* Floating Button */}
            {!isOpen && (
                <button
                    onClick={toggleWidget}
                    className="fixed bottom-5 right-5 w-16 h-16 bg-[#90243C] hover:bg-[#701020] text-white rounded-full shadow-2xl flex items-center justify-center transition-all duration-300 hover:scale-110 z-[99999] group"
                    style={{
                        boxShadow: '0 10px 40px rgba(37, 99, 235, 0.4), 0 0 20px rgba(37, 99, 235, 0.2)',
                    }}
                    title="Open CampusBot"
                >
                    <MessageCircle className="w-7 h-7 transition-transform group-hover:scale-110" strokeWidth={2.5} />

                    {/* Pulse rings */}
                    <span className="absolute inset-0 rounded-full bg-[#90243C] animate-ping opacity-20"></span>
                    <span className="absolute inset-0 rounded-full bg-[#90243C] animate-pulse opacity-10"></span>

                    {/* Badge for unread (optional) */}
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-[10px] font-bold flex items-center justify-center shadow-lg animate-bounce">
                        !
                    </span>
                </button>
            )}

            {/* Widget Window */}
            {isOpen && (
                <>
                    {/* Mobile overlay */}
                    <div
                        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[99998] md:hidden transition-opacity duration-300"
                        onClick={closeWidget}
                        style={{ opacity: isAnimating ? 0 : 1 }}
                    />

                    <div
                        className={`fixed bottom-5 right-5 bg-white rounded-2xl z-[99999] transition-all duration-300 ease-out origin-bottom-right ${isMinimized
                            ? 'w-80 h-16 shadow-lg'
                            : 'w-[420px] h-[680px] shadow-2xl'
                            } ${isAnimating ? 'opacity-0 scale-95 translate-y-4' : 'opacity-100 scale-100 translate-y-0'}`}
                        style={{
                            maxHeight: 'calc(100vh - 40px)',
                            maxWidth: 'calc(100vw - 40px)',
                            boxShadow: isMinimized
                                ? '0 4px 20px rgba(0,0,0,0.1)'
                                : '0 20px 60px rgba(0,0,0,0.2), 0 0 1px rgba(0,0,0,0.1)',
                        }}
                    >
                        {/* Widget Header */}
                        <div className="bg-[#90243C] text-white px-5 py-4 rounded-t-2xl flex items-center justify-between shadow-lg">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                                    <MessageCircle className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-base">CampusBot</h3>
                                    <p className="text-xs text-white/80">Your AI Assistant</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-1">
                                {!isMinimized ? (
                                    <>
                                        <button
                                            onClick={minimizeWidget}
                                            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                                            title="Minimize"
                                        >
                                            <Minus className="w-4 h-4" strokeWidth={2.5} />
                                        </button>
                                        <button
                                            onClick={closeWidget}
                                            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                                            title="Close"
                                        >
                                            <X className="w-4 h-4" strokeWidth={2.5} />
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <button
                                            onClick={expandWidget}
                                            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                                            title="Expand"
                                        >
                                            <Maximize2 className="w-4 h-4" strokeWidth={2.5} />
                                        </button>
                                        <button
                                            onClick={closeWidget}
                                            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                                            title="Close"
                                        >
                                            <X className="w-4 h-4" strokeWidth={2.5} />
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* Widget Content */}
                        {!isMinimized && (
                            <div className="h-[calc(100%-72px)] overflow-hidden">
                                {isAuthenticated ? (
                                    <ChatProvider>
                                        <ChatWidget />
                                    </ChatProvider>
                                ) : (
                                    <LoginWidget />
                                )}
                            </div>
                        )}

                        {/* Minimized state message */}
                        {isMinimized && (
                            <div className="px-5 py-2 text-sm text-gray-600 truncate">
                                Click to expand and continue chatting...
                            </div>
                        )}
                    </div>
                </>
            )}
        </>
    );
};


export default WidgetContainer;

