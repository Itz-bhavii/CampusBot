import { BookOpen, LogOut, RotateCcw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';

const Header = () => {
    const { logout } = useAuth();
    const { resetChat } = useChat();

    return (
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-3">
                <div className="bg-blue-600 p-2 rounded-lg">
                    <BookOpen className="w-5 h-5 text-white" />
                </div>
                <div>
                    <h1 className="text-lg font-bold text-slate-900">CampusBot</h1>
                    <p className="text-xs text-slate-600">Campus Knowledge Assistant</p>
                </div>
            </div>

            <div className="flex items-center gap-2">
                <button
                    onClick={resetChat}
                    className="flex items-center gap-2 px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg transition-colors text-sm font-medium"
                    title="Start new conversation"
                >
                    <RotateCcw className="w-4 h-4" />
                    <span className="hidden sm:inline">New Chat</span>
                </button>

                <button
                    onClick={logout}
                    className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors text-sm font-medium"
                    title="Logout"
                >
                    <LogOut className="w-4 h-4" />
                    <span className="hidden sm:inline">Logout</span>
                </button>
            </div>
        </header>
    );
};

export default Header;
