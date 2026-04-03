import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { onAuthStateChanged, signOut, type User } from 'firebase/auth';
import { auth } from '../lib/firebase';

interface AuthContextType {
    token: string | null;
    user: User | null;
    logout: () => void;
    isAuthenticated: boolean;
    loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [token, setToken] = useState<string | null>(null);
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            if (firebaseUser) {
                const idToken = await firebaseUser.getIdToken();
                setToken(idToken);
                setUser(firebaseUser);
                localStorage.setItem('token', idToken);
            } else {
                setToken(null);
                setUser(null);
                localStorage.removeItem('token');
            }
            setLoading(false);
        });
        return unsubscribe;
    }, []);

    // Refresh token every 50 minutes (Firebase tokens expire in 60 min)
    useEffect(() => {
        if (!user) return;
        const interval = setInterval(async () => {
            const freshToken = await user.getIdToken(true);
            setToken(freshToken);
            localStorage.setItem('token', freshToken);
        }, 50 * 60 * 1000);
        return () => clearInterval(interval);
    }, [user]);

    const logout = async () => {
        await signOut(auth);
        setToken(null);
        setUser(null);
        localStorage.removeItem('token');
    };

    return (
        <AuthContext.Provider value={{ token, user, logout, isAuthenticated: !!token, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
