import { ArrowRight, BookOpen, GraduationCap, Users } from 'lucide-react';

const LandingPage = () => {
    return (
        <div className="font-sans text-slate-900">
            {/* Navigation Bar */}
            <nav className="bg-white py-3 px-6 md:px-12 flex items-center justify-between shadow-sm sticky top-0 z-40">
                <div className="flex items-center gap-2">
                    <div className="flex flex-col">
                        <h1 className="text-2xl font-bold text-[#800000] leading-none tracking-tight">MIT</h1>
                        <p className="text-[10px] text-slate-600 font-bold uppercase tracking-wide leading-tight mt-0.5">Arts, Commerce<br />& Science College</p>
                    </div>
                </div>

                <div className="hidden lg:flex items-center gap-6 text-sm font-medium text-slate-700">
                    <a href="#" className="hover:text-[#800000] flex items-center gap-1">About <span className="text-[10px]">▼</span></a>
                    <a href="#" className="hover:text-[#800000] flex items-center gap-1">Admissions <span className="text-[10px]">▼</span></a>
                    <a href="#" className="hover:text-[#800000] flex items-center gap-1">Academics <span className="text-[10px]">▼</span></a>
                    <a href="#" className="hover:text-[#800000] flex items-center gap-1">Placement <span className="text-[10px]">▼</span></a>
                    <a href="#" className="hover:text-[#800000] flex items-center gap-1">Students Corner <span className="text-[10px]">▼</span></a>
                    <a href="#" className="hover:text-[#800000] flex items-center gap-1">Research <span className="text-[10px]">▼</span></a>
                    <a href="#" className="hover:text-[#800000] flex items-center gap-1">IQAC/SSR <span className="text-[10px]">▼</span></a>
                    <a href="#" className="hover:text-[#800000]">Contact</a>
                </div>

                <button className="bg-[#90243C] text-white px-5 py-2 text-sm font-semibold shadow-md hover:bg-[#701020] transition-colors">
                    Apply<br />Now
                </button>
            </nav>

            {/* Hero Section */}
            <section className="bg-[#FFF5F5] min-h-[600px] flex items-center relative overflow-hidden px-6 md:px-12 py-12">
                <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center w-full">
                    {/* Left Content */}
                    <div className="relative z-10 flex flex-col gap-6">
                        <h2 className="text-[#90243C] font-bold text-3xl md:text-4xl">
                            Admissions Open for 2026-27
                        </h2>

                        <h1 className="text-4xl md:text-5xl font-serif text-slate-900 font-medium leading-tight">
                            Apply Now for UG & PG Programs at MIT ACSC
                        </h1>

                        <p className="text-slate-700 text-lg max-w-xl">
                            Shape your future with transformative undergraduate and postgraduate education.
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                            <div className="bg-white p-6 rounded-lg shadow-sm flex flex-col items-center text-center gap-3">
                                <GraduationCap className="w-8 h-8 text-orange-400" />
                                <span className="font-medium text-slate-800">Industry-Ready Curriculum</span>
                            </div>
                            <div className="bg-white p-6 rounded-lg shadow-sm flex flex-col items-center text-center gap-3">
                                <Users className="w-8 h-8 text-orange-400" />
                                <span className="font-medium text-slate-800">Expert Faculty & Global Exposure</span>
                            </div>
                            <div className="bg-white p-6 rounded-lg shadow-sm flex flex-col items-center text-center gap-3">
                                <BookOpen className="w-8 h-8 text-orange-400" />
                                <span className="font-medium text-slate-800">Strong Placement Network</span>
                            </div>
                        </div>

                        <div className="mt-6">
                            <button className="bg-[#90243C] text-white px-8 py-3 font-semibold rounded shadow-md hover:bg-[#701020] transition-colors">
                                Apply Now
                            </button>
                        </div>
                    </div>

                    {/* Right Image */}
                    <div className="relative z-10 flex justify-center lg:justify-end">
                        <div className="relative w-full max-w-md bg-[#800000] rounded-none">
                            {/* Image Placeholder - using a div to represent the student image position */}
                            <div className="w-full h-[500px] bg-slate-200 overflow-hidden relative">
                                <img
                                    src="https://images.unsplash.com/photo-1523240795612-9a054b0db644?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80"
                                    alt="Student"
                                    className="w-full h-full object-cover"
                                />
                                {/* Red background shape behind logic would require absolute positioning or proper image compositing */}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Awards & Achievements Section */}
            <section className="py-16 px-6 md:px-12 bg-white">
                <div className="flex flex-col lg:flex-row gap-8 items-start">
                    {/* Left Title */}
                    <div className="lg:w-1/4">
                        <div className="text-[#90243C] mb-4">
                            <svg width="60" height="60" viewBox="0 0 24 24" fill="currentColor" className="mx-0">
                                <path d="M12 2C15.866 2 19 5.13401 19 9C19 12.866 15.866 16 12 16C8.13401 16 5 12.866 5 9C5 5.13401 8.13401 2 12 2ZM12 4C9.23858 4 7 6.23858 7 9C7 11.7614 9.23858 14 12 14C14.7614 14 17 11.7614 17 9C17 6.23858 14.7614 4 12 4Z" opacity="0.5" />
                                <path d="M19 9C19 11.8954 16.6528 14.4173 14 15.424V19H16V21H8V19H10V15.424C7.34721 14.4173 5 11.8954 5 9C5 8.15041 5.215 7.34731 5.59477 6.63588C4.04167 7.20811 3 8.65084 3 10.5C3 12.9853 5.01472 15 7.5 15C8.36012 15 9.16335 14.757 9.85172 14.335C10.4905 14.7525 11.2215 15 12 15C12.7785 15 13.5095 14.7525 14.1483 14.335C14.8367 14.757 15.6399 15 16.5 15C18.9853 15 21 12.9853 21 10.5C21 8.65084 19.9583 7.20811 18.4052 6.63588C18.785 7.34731 19 8.15041 19 9Z" />
                            </svg>
                        </div>
                        <h2 className="text-4xl font-serif text-slate-900 leading-tight">
                            Awards &<br />Achievements
                        </h2>
                    </div>

                    {/* Right Cards */}
                    <div className="lg:w-3/4 grid grid-cols-1 md:grid-cols-4 gap-0">
                        {/* Card 1 */}
                        <div className="bg-[#90243C] text-white p-8 flex flex-col justify-between h-80 transition-transform hover:-translate-y-2">
                            <div>
                                <h3 className="text-xl font-bold mb-4">Best Placement Among Educational Institutions</h3>
                                <p className="text-white/80 text-sm">Pune, Maharashtra (By Brands Academy)</p>
                            </div>
                            <button className="self-start">
                                <ArrowRight className="w-6 h-6" />
                            </button>
                        </div>

                        {/* Card 2 */}
                        <div className="bg-[#F59E0B] text-white p-8 flex flex-col justify-between h-80 transition-transform hover:-translate-y-2">
                            <div>
                                <h3 className="text-xl font-bold mb-4">Best College Rankings 2025</h3>
                                <p className="text-white/90 text-sm">Ranked Among India's Top Institutions by MDFA<br />Featured in the Prestigious India Today Edition</p>
                            </div>
                            <button className="self-start">
                                <ArrowRight className="w-6 h-6" />
                            </button>
                        </div>

                        {/* Card 3 */}
                        <div className="bg-[#90243C] text-white p-8 flex flex-col justify-between h-80 transition-transform hover:-translate-y-2">
                            <div>
                                <h3 className="text-xl font-bold mb-4">Best Educationist Award</h3>
                                <p className="text-white/80 text-sm">By International Institute of Education & Management, New Delhi</p>
                            </div>
                            <button className="self-start">
                                <ArrowRight className="w-6 h-6" />
                            </button>
                        </div>

                        {/* Card 4 */}
                        <div className="bg-[#F59E0B] text-white p-8 flex flex-col justify-between h-80 transition-transform hover:-translate-y-2">
                            <div>
                                <h3 className="text-xl font-bold mb-4">University Level Best College Award</h3>
                                <p className="text-white/90 text-sm">From Savitribai Phule Pune University for Student Development Activities</p>
                            </div>
                            <button className="self-start">
                                <ArrowRight className="w-6 h-6" />
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Notice Board and News (Simplified for layout match) */}
            <section className="py-12 px-6 md:px-12 grid grid-cols-1 md:grid-cols-2 gap-12">
                <div>
                    <h2 className="text-3xl font-serif text-slate-900 mb-6">Notice Board</h2>
                    <div className="border border-slate-200 rounded p-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className="bg-green-500 rounded-full p-2">
                                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
                            </span>
                            <span className="font-semibold text-sm">CTE October 2025 Exam held in February 2026 (FYBBA-CA)</span>
                            <span className="bg-[#90243C] text-white text-[10px] px-1 rounded">NEW</span>
                        </div>
                    </div>
                </div>
                <div>
                    <h2 className="text-3xl font-serif text-slate-900 mb-6">News & Events</h2>
                    <div className="flex gap-4">
                        <div className="bg-[#F59E0B] text-white p-4 flex flex-col items-center justify-center w-24 text-center shrink-0">
                            <span className="text-lg font-bold">JAN</span>
                            <span className="text-2xl font-bold">2026</span>
                        </div>
                        <div>
                            <p className="text-slate-800 font-medium">Our distinguished alumni, Mr. Adinath Lendve and Ms. Gargi Jadhav from BBA and BBA-IB, on successfully completing their M.Sc. in...</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Side Admission Enquiry Tab (placeholder for the vertical tab seen in images) */}
            <div className="fixed top-1/2 right-0 -translate-y-1/2 bg-[#1e1e2d] text-white py-4 px-2 rounded-l-md z-30 cursor-pointer writing-vertical-rl transform rotate-180 flex items-center justify-center gap-2 shadow-lg h-40">
                <span className="text-sm font-semibold tracking-wide" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>Admission Enquiry</span>
            </div>

        </div>
    );
};

export default LandingPage;
