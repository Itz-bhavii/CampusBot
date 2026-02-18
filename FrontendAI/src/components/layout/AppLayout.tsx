import type { ReactNode } from 'react';
import Sidebar from './Sidebar';

interface AppLayoutProps {
    children: ReactNode;
}

const AppLayout = ({ children }: AppLayoutProps) => {
    return (
        <div className="min-h-screen bg-gray-950 text-white flex">
            <Sidebar />
            <main className="flex-1 ml-64 relative min-h-screen w-full">
                <div className="max-w-4xl mx-auto h-full flex flex-col p-4 md:p-6 lg:p-8">
                    {children}
                </div>

                {/* Background Gradients */}
                <div className="fixed inset-0 pointer-events-none z-0">
                    <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[120px]" />
                    <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[120px]" />
                </div>
            </main>
        </div>
    );
};

export default AppLayout;
