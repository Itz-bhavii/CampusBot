import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor - adds JWT token to every request
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            // Clean token: remove quotes and whitespace that might have been stored
            const cleanToken = token.replace(/^["']|["']$/g, '').trim();
            config.headers.Authorization = `Bearer ${cleanToken}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - handles token expiration and errors
api.interceptors.response.use(
    (response) => {
        // Success response - pass through
        return response;
    },
    (error) => {
        // Handle 401 Unauthorized (token expired or invalid)
        if (error.response?.status === 401) {
            // Only redirect to login if we're not already on the login page
            // and if we're not on the /authenticate endpoint
            const isAuthEndpoint = error.config?.url?.includes('/authenticate');
            const isOnLoginPage = window.location.pathname === '/';
            
            if (!isAuthEndpoint && !isOnLoginPage) {
                console.error('Token expired or invalid. Redirecting to login...');
                localStorage.removeItem('token');
                window.location.href = '/';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
