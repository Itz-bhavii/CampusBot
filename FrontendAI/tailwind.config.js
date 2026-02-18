/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                indigo: {
                    950: '#1e1b4b',
                    900: '#312e81',
                    800: '#3730a3',
                    700: '#4338ca',
                    600: '#4f46e5',
                    500: '#6366f1',
                    400: '#818cf8',
                    300: '#a5b4fc',
                    200: '#c7d2fe',
                    100: '#e0e7ff',
                    50: '#eef2ff',
                }
            }
        },
    },
    plugins: [],
}
