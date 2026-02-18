import { useState, useRef } from 'react';
import { Send, Paperclip, X, FileText } from 'lucide-react';

const InputArea = ({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) => {
    const [input, setInput] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !disabled) {
            onSend(input);
            setInput('');
        }
    };

    const handleFileClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            // TODO: Implement actual file upload to backend /api/ingest endpoint
            console.log('File selected:', file.name);
            // For now, notify user via message
            onSend(`[Document uploaded: ${file.name}]\n\nWhat would you like to know about this document?`);
            // Clear after a moment
            setTimeout(() => setSelectedFile(null), 2000);
        }
    };

    const clearFile = () => {
        setSelectedFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div className="w-full">
            {/* File preview */}
            {selectedFile && (
                <div className="mb-2 flex items-center gap-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
                    <span className="text-sm text-slate-700 flex-1 truncate">{selectedFile.name}</span>
                    <button
                        onClick={clearFile}
                        className="text-slate-400 hover:text-slate-700 p-1"
                        type="button"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            <form onSubmit={handleSubmit} className="relative">
                <div className="flex items-end gap-2 bg-white rounded-xl border-2 border-slate-200 focus-within:border-blue-500 transition-colors p-2 shadow-sm">
                    <button
                        type="button"
                        onClick={handleFileClick}
                        disabled={disabled}
                        className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
                        title="Upload document (PDF, DOC, TXT)"
                    >
                        <Paperclip className="w-5 h-5" />
                    </button>
                    
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.doc,.docx,.txt"
                        onChange={handleFileChange}
                        className="hidden"
                    />

                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                        placeholder="Ask about campus policies, regulations, schedules..."
                        disabled={disabled}
                        rows={1}
                        className="flex-1 bg-transparent text-slate-900 placeholder-slate-400 px-2 py-2 focus:outline-none resize-none max-h-32 scrollbar-thin scrollbar-thumb-slate-300 disabled:opacity-50"
                        style={{ minHeight: '24px' }}
                    />
                    
                    <button
                        type="submit"
                        disabled={disabled || !input.trim()}
                        className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex-shrink-0"
                        title="Send message"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
                
                <p className="text-xs text-slate-500 mt-2 text-center">
                    Press Enter to send • Shift+Enter for new line • Click 📎 to upload documents
                </p>
            </form>
        </div>
    );
};

export default InputArea;
