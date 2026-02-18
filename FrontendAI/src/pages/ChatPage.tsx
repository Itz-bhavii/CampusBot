import ChatWindow from '../components/chat/ChatWindow';
import Header from '../components/layout/Header';
import { ChatProvider } from '../context/ChatContext';

const ChatPage = () => {
    return (
        <ChatProvider>
            <div className="flex flex-col h-screen bg-slate-50">
                <Header />
                <div className="flex-1 overflow-hidden">
                    <ChatWindow />
                </div>
            </div>
        </ChatProvider>
    );
};

export default ChatPage;
