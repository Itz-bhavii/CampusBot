import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { BookOpen, Lock, ArrowRight } from 'lucide-react';
import api from '../../lib/api';

const LoginWidget = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [focusedField, setFocusedField] = useState('');
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        localStorage.removeItem('token');

        try {
            const response = await api.post('/authenticate', { username, password });

            let token = response.data;
            if (typeof token === 'object' && token !== null && 'token' in token) {
                token = token.token;
            }
            if (typeof token === 'string') {
                token = token.replace(/^["']|["']$/g, '').trim();
            } else {
                token = String(token);
            }

            if (!token || token.split('.').length !== 3) {
                setError('Invalid token received');
                setLoading(false);
                return;
            }

            setTimeout(() => {
                login(token);
            }, 1000);

        } catch (err: any) {
            setLoading(false);
            if (err.response?.status === 401 || err.response?.status === 403) {
                setError('Invalid student ID or password');
            } else if (err.code === 'ERR_NETWORK') {
                setError('Cannot connect to server');
            } else {
                setError('Login failed. Please try again');
            }
        }
    };

    return (

        <div className="h-full flex flex-col p-8 overflow-y-auto bg-gradient-to-br from-gray-50 to-white">
            {/* Welcome section */}
            <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-[#90243C] rounded-2xl mb-4 shadow-lg shadow-[#90243C]/30">
                    <BookOpen className="w-10 h-10 text-white" strokeWidth={2} />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">CampusBot Login</h2>
                <p className="text-gray-600">Enter your credentials to continue</p>
            </div>

            {/* Login form */}
            <form onSubmit={handleSubmit} className="space-y-5 flex-1">
                <div>
                    <label
                        htmlFor="username"
                        className="block text-sm font-semibold text-gray-700 mb-2"
                    >
                        Student ID
                    </label>
                    <div className={`relative transition-all duration-200 ${focusedField === 'username' ? 'scale-[1.01]' : ''}`}>
                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            onFocus={() => setFocusedField('username')}
                            onBlur={() => setFocusedField('')}
                            required
                            className="w-full px-4 py-3.5 bg-white border-2 border-gray-200 rounded-xl text-gray-900 text-sm placeholder-gray-400 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 transition-all"
                            placeholder="Enter your student ID"
                        />
                    </div>
                </div>

                <div>
                    <label
                        htmlFor="password"
                        className="block text-sm font-semibold text-gray-700 mb-2"
                    >
                        Password
                    </label>
                    <div className={`relative transition-all duration-200 ${focusedField === 'password' ? 'scale-[1.01]' : ''}`}>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            onFocus={() => setFocusedField('password')}
                            onBlur={() => setFocusedField('')}
                            required
                            className="w-full px-4 py-3.5 bg-white border-2 border-gray-200 rounded-xl text-gray-900 text-sm placeholder-gray-400 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 transition-all"
                            placeholder="Enter your password"
                        />
                    </div>
                </div>

                {error && (
                    <div className="p-4 bg-red-50 border-2 border-red-200 rounded-xl animate-shake">
                        <p className="text-sm text-red-700 font-medium">{error}</p>
                    </div>
                )}

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-4 px-6 bg-[#90243C] hover:bg-[#701020] text-white font-semibold rounded-xl transition-all shadow-lg shadow-[#90243C]/30 hover:shadow-xl hover:shadow-[#90243C]/40 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-lg flex items-center justify-center gap-2 group"
                >
                    {loading ? (
                        <>
                            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>Signing in...</span>
                        </>
                    ) : (
                        <>
                            <span>Sign In</span>
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" strokeWidth={2.5} />
                        </>
                    )}
                </button>
            </form>

            {/* Footer */}
            <div className="mt-8 pt-6 border-t border-gray-200">
                <div className="flex items-center gap-3 text-xs text-gray-600">
                    <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                        <Lock className="w-4 h-4 text-gray-600" strokeWidth={2} />
                    </div>
                    <p className="leading-relaxed">
                        Secure login for students and faculty. Need help? Contact <span className="font-semibold text-blue-600">IT support</span>.
                    </p>
                </div>
            </div>

            <style>{`
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-5px); }
                    75% { transform: translateX(5px); }
                }
                .animate-shake {
                    animation: shake 0.3s ease-in-out;
                }
            `}</style>
        </div>
    );
};

export default LoginWidget;
