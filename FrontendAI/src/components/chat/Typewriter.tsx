import { useState, useEffect } from 'react';

interface TypewriterProps {
    text: string;
    delay?: number;
}

const Typewriter = ({ text, delay = 15 }: TypewriterProps) => {
    const [currentText, setCurrentText] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        setCurrentText('');
        setCurrentIndex(0);
    }, [text]);

    useEffect(() => {
        if (currentIndex < text.length) {
            const timeout = setTimeout(() => {
                setCurrentText(prev => prev + text[currentIndex]);
                setCurrentIndex(prev => prev + 1);
            }, delay);

            return () => clearTimeout(timeout);
        }
    }, [currentIndex, delay, text]);

    return <span className="text-sm leading-relaxed whitespace-pre-wrap break-words">{currentText}</span>;
};

export default Typewriter;
