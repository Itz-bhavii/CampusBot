import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookOpen, Shield } from 'lucide-react';
import api from '../lib/api';

const LoginPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        localStorage.removeItem('token');

        try {
            console.log('Attempting login for user:', username);
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
                console.error('Invalid JWT token format:', token);
                setError('Login failed: Invalid token received from server');
                return;
            }
            
            login(token);
            console.log('Token stored, navigating to chat...');
            navigate('/chat');
        } catch (err: any) {
            console.error('Login error:', err);
            if (err.response?.status === 401 || err.response?.status === 403) {
                setError('Invalid username or password');
            } else if (err.code === 'ERR_NETWORK') {
                setError('Cannot connect to server');
            } else {
                setError('Login failed. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
            <div className="w-full max-w-5xl grid md:grid-cols-2 gap-8 items-center">
                {/* Left side - Branding */}
                <div className="hidden md:block">
                    <div className="bg-white rounded-2xl p-8 shadow-lg border border-slate-200">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="bg-blue-600 p-3 rounded-xl">
                                <BookOpen className="w-8 h-8 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-slate-900">CampusBot</h1>
                                <p className="text-sm text-slate-600">Campus Knowledge Assistant</p>
                            </div>
                        </div>
                        
                        <div className="space-y-4 mt-8">
                            <div className="flex items-start gap-3">
                                <div className="bg-blue-100 p-2 rounded-lg mt-1">
                                    <Shield className="w-4 h-4 text-blue-600" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-slate-900 mb-1">Secure Access</h3>
                                    <p className="text-sm text-slate-600">Login with your student credentials to access campus resources</p>
                                </div>
                            </div>
                            
                            <div className="flex items-start gap-3">
                                <div className="bg-green-100 p-2 rounded-lg mt-1">
                                    <BookOpen className="w-4 h-4 text-green-600" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-slate-900 mb-1">Instant Answers</h3>
                                    <p className="text-sm text-slate-600">Get quick answers about campus policies, schedules, and resources</p>
                                </div>
                            </div>
                            
                            <div className="flex items-start gap-3">
                                <div className="bg-purple-100 p-2 rounded-lg mt-1">
                                    <svg className="w-4 h-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-slate-900 mb-1">Document Analysis</h3>
                                    <p className="text-sm text-slate-600">Upload and query your own documents for personalized assistance</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right side - Login form */}
                <div className="w-full">
                    <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-200">
                        <div className="mb-6">
                            <h2 className="text-2xl font-bold text-slate-900 mb-2">Student Login</h2>
                            <p className="text-slate-600">Enter your credentials to continue</p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label htmlFor="username" className="block text-sm font-medium text-slate-700 mb-2">
                                    Student ID / Username
                                </label>
                                <input
                                    id="username"
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                    placeholder="Enter your student ID"
                                />
                            </div>

                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-2">
                                    Password
                                </label>
                                <input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                    placeholder="Enter your password"
                                />
                            </div>

                            {error && (
                                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                                    <p className="text-sm text-red-700">{error}</p>
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                            >
                                {loading ? 'Signing in...' : 'Sign In'}
                            </button>
                        </form>

                        <div className="mt-6 pt-6 border-t border-slate-200">
                            <p className="text-xs text-slate-500 text-center">
                                This is a secure portal for students and faculty. 
                                <br />Contact IT support if you need assistance.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
