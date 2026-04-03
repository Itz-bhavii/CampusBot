import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookOpen, Shield } from 'lucide-react';
import { signInWithPopup, signInWithEmailAndPassword } from 'firebase/auth';
import { auth, googleProvider } from '../lib/firebase';

const LoginPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();

    // Redirect if already authenticated
    if (isAuthenticated) {
        navigate('/chat');
        return null;
    }

    const handleGoogleSignIn = async () => {
        setLoading(true);
        setError('');
        try {
            await signInWithPopup(auth, googleProvider);
            navigate('/chat');
        } catch (err: any) {
            console.error('Google sign-in error:', err);
            setError(err.message || 'Google sign-in failed');
        } finally {
            setLoading(false);
        }
    };

    const handleEmailSignIn = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await signInWithEmailAndPassword(auth, email, password);
            navigate('/chat');
        } catch (err: any) {
            console.error('Email sign-in error:', err);
            if (err.code === 'auth/invalid-credential' || err.code === 'auth/wrong-password') {
                setError('Invalid email or password');
            } else if (err.code === 'auth/user-not-found') {
                setError('No account found with this email');
            } else {
                setError(err.message || 'Sign in failed');
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
                                    <p className="text-sm text-slate-600">Sign in with Google or email to access campus resources</p>
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

                {/* Right side - Login */}
                <div className="w-full">
                    <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-200">
                        <div className="mb-6">
                            <h2 className="text-2xl font-bold text-slate-900 mb-2">Welcome</h2>
                            <p className="text-slate-600">Sign in to continue to CampusBot</p>
                        </div>

                        {/* Google Sign-In Button */}
                        <button
                            onClick={handleGoogleSignIn}
                            disabled={loading}
                            className="w-full py-3 px-4 bg-white hover:bg-slate-50 text-slate-700 font-medium rounded-lg transition-all shadow-sm border border-slate-300 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 mb-6"
                        >
                            <svg className="w-5 h-5" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                            </svg>
                            Continue with Google
                        </button>

                        <div className="relative mb-6">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-slate-200" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-white text-slate-500">or sign in with email</span>
                            </div>
                        </div>

                        <form onSubmit={handleEmailSignIn} className="space-y-5">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">
                                    Email
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                    placeholder="you@example.com"
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
                                {loading ? 'Signing in...' : 'Sign In with Email'}
                            </button>
                        </form>

                        <div className="mt-6 pt-6 border-t border-slate-200">
                            <p className="text-xs text-slate-500 text-center">
                                Powered by Firebase Authentication.
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
