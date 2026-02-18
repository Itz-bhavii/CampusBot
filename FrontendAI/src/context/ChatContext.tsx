import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import api from '../lib/api';

interface Message {
    id: string;
    sender: 'user' | 'bot';
    text: string;
    timestamp: Date;
}

interface ChatContextType {
    messages: Message[];
    conversationId: string | null;
    sendMessage: (text: string) => Promise<void>;
    resetChat: () => void;
    isLoading: boolean;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const sendMessage = async (text: string) => {
        // Validate input
        if (!text || text.trim() === '') {
            console.warn('Empty message not sent');
            return;
        }

        // Add user message immediately for better UX
        const userMessage: Message = {
            id: crypto.randomUUID(),
            sender: 'user',
            text: text.trim(),
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);
        setIsLoading(true);

        try {
            // Prepare payload for Spring Boot backend
            const payload = {
                conversationId: conversationId, // null for first message, UUID string for subsequent
                message: text.trim(),
            };

            console.log('Sending message to /api/chat:', payload);

            // Call Spring Boot /api/chat endpoint
            const response = await api.post('/chat', payload);

            console.log('Chat response received:', response.data);

            const data = response.data;

            // Update conversation ID if provided (first message creates new conversation)
            if (data.conversationId && data.conversationId !== conversationId) {
                setConversationId(data.conversationId);
                console.log('Conversation ID set:', data.conversationId);
            }

            // Add bot response message
            const botMessage: Message = {
                id: crypto.randomUUID(),
                sender: 'bot',
                text: data.message || data.response || "I'm sorry, I couldn't generate a response.",
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, botMessage]);
        } catch (error: any) {
            console.error("Failed to send message:", error);
            console.error("Error response:", error.response?.data);
            
            // User-friendly error messages
            let errorText = "Error: Could not connect to server.";
            
            if (error.response?.status === 401) {
                errorText = "Authentication failed. Please log in again.";
                // Trigger logout on auth failure
                setTimeout(() => {
                    localStorage.removeItem('token');
                    window.location.href = '/';
                }, 2000);
            } else if (error.response?.status === 500) {
                errorText = "Server error. Please try again later.";
            } else if (error.code === 'ERR_NETWORK') {
                errorText = "Cannot reach server. Check your connection.";
            } else if (error.response?.data?.message) {
                errorText = `Error: ${error.response.data.message}`;
            }
            
            const errorMessage: Message = {
                id: crypto.randomUUID(),
                sender: 'bot',
                text: errorText,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const resetChat = () => {
        setConversationId(null);
        setMessages([]);
    };

    return (
        <ChatContext.Provider value={{ messages, conversationId, sendMessage, resetChat, isLoading }}>
            {children}
        </ChatContext.Provider>
    );
};

export const useChat = () => {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error('useChat must be used within a ChatProvider');
    }
    return context;
};
