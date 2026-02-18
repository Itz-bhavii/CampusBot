import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface AuthContextType {
    token: string | null;
    login: (token: string) => void;
    logout: () => void;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {

    // Initialize state as null, we'll clear it in useEffect
    const [token, setToken] = useState<string | null>(null);

    useEffect(() => {
        // Clear token on initial mount to ensure user is logged out on refresh/first visit
        console.log('Clearing auth token on initial load');
        localStorage.removeItem('token');
        setToken(null);
    }, []);

    // Sync token changes to localStorage
    useEffect(() => {
        if (token) {
            // Always store clean token
            const cleanToken = token.replace(/^["']|["']$/g, '').trim();
            localStorage.setItem('token', cleanToken);
            console.log('Token persisted to localStorage');
        } else {
            localStorage.removeItem('token');
            console.log('Token removed from localStorage');
        }
    }, [token]);

    const login = (newToken: string) => {
        console.log('Login called with token:', newToken);
        // Clean token before storing
        const cleanToken = newToken.replace(/^["']|["']$/g, '').trim();
        setToken(cleanToken);
    };

    const logout = () => {
        console.log('Logout called');
        setToken(null);
        // Clear all auth-related data
        localStorage.removeItem('token');
        // Don't redirect - let the widget handle it
    };

    return (
        <AuthContext.Provider value={{ token, login, logout, isAuthenticated: !!token }}>
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
