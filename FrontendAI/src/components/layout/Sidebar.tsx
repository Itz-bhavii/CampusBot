import { Plus, MessageSquare, LogOut } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useAuth } from '../../context/AuthContext';

const Sidebar = () => {
    const { resetChat } = useChat();
    const { logout } = useAuth();

    return (
        <div className="fixed left-0 top-0 h-full w-64 flex flex-col glass-effect border-r border-white/10 z-20">
            <div className="p-6">
                <div className="flex items-center gap-3 mb-8">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
                        <MessageSquare className="w-5 h-5 text-white" />
                    </div>
                    <h1 className="text-xl font-bold text-white tracking-wide">CampusBot</h1>
                </div>

                <button
                    onClick={resetChat}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition-all shadow-lg shadow-indigo-500/20 group border border-indigo-400/30"
                >
                    <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform" />
                    <span className="font-medium">New Chat</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-2">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-4 px-2">
                    Recent
                </div>
                {/* History items would go here */}
                <div className="text-sm text-gray-400 px-2 italic">
                    No recent history
                </div>
            </div>

            <div className="p-4 border-t border-white/5 space-y-2">
                <div className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-400 to-purple-400 flex items-center justify-center text-xs font-bold text-white">
                        U
                    </div>
                    <div className="text-sm">
                        <div className="font-medium text-white">User</div>
                        <div className="text-xs text-gray-400">Student</div>
                    </div>
                </div>
                
                <button
                    onClick={logout}
                    className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-red-500/10 text-red-400 hover:text-red-300 transition-all group border border-transparent hover:border-red-500/30"
                >
                    <LogOut className="w-4 h-4" />
                    <span className="text-sm font-medium">Logout</span>
                </button>
            </div>

            <style>{`
        .glass-effect {
          background: rgba(30, 27, 75, 0.7);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
        }
      `}</style>
        </div>
    );
};

export default Sidebar;
