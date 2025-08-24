"use client";

import React, { useState, useEffect } from 'react';
import { ChevronRight, MessageSquare, FileText, UserCheck, Calendar, Menu, X, ArrowRight } from 'lucide-react';
import Link from 'next/link';

const Home = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  const colors = {
    primary: '#095d7e',
    secondary: '#ccecee',
    background: '#f1f9ff'
  };

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const features = [
    {
      icon: MessageSquare,
      title: "Smart Patient Follow-ups",
      description: "Automated WhatsApp reminders and follow-up requests that keep patients engaged in their care journey."
    },
    {
      icon: FileText,
      title: "AI Report Analysis",
      description: "Patients upload reports and images, AI extracts readings and generates comprehensive graphs automatically."
    },
    {
      icon: UserCheck,
      title: "Doctor In Loop",
      description: "AI drafts intelligent responses, but doctors review and edit everything before sending to ensure quality care."
    },
    {
      icon: Calendar,
      title: "Seamless Appointments",
      description: "Google Calendar integration makes booking and managing follow-up appointments effortless for everyone."
    }
  ];

  return (
    <div className="min-h-screen" style={{ backgroundColor: colors.background }}>
      {/* Navigation */}
      <nav className={`fixed w-full z-50 transition-all duration-500 ${
        isScrolled ? 'backdrop-blur-lg shadow-lg' : 'bg-transparent'
      }`} style={isScrolled ? { backgroundColor: 'rgba(255, 255, 255, 0.8)' } : {}}>
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            {/* Logo */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: colors.primary }}>
                <MessageSquare className="w-5 h-5" style={{ color: colors.background }} />
              </div>
              <span className="text-xl font-bold" style={{ color: colors.primary }}>DocFollow</span>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <a 
                href="#features" 
                className="text-gray-600 transition-colors duration-300"
                style={{ color: '#4b5563' }}
                onMouseEnter={(e) => e.currentTarget.style.color = colors.primary}
                onMouseLeave={(e) => e.currentTarget.style.color = '#4b5563'}
              >
                Features
              </a>
              {/* <a 
                href="#" 
                className="text-gray-600 transition-colors duration-300"
                style={{ color: '#4b5563' }}
                onMouseEnter={(e) => e.currentTarget.style.color = colors.primary}
                onMouseLeave={(e) => e.currentTarget.style.color = '#4b5563'}
              >
                About
              </a> */}
              {/* <a 
                href="#" 
                className="text-gray-600 transition-colors duration-300"
                style={{ color: '#4b5563' }}
                onMouseEnter={(e) => e.currentTarget.style.color = colors.primary}
                onMouseLeave={(e) => e.currentTarget.style.color = '#4b5563'}
              >
                Contact
              </a> */}
              <Link 
                className="px-6 py-2 rounded-full font-medium transition-all duration-300 hover:shadow-lg hover:scale-105"
                style={{ backgroundColor: colors.primary, color: colors.background }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#074a61'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = colors.primary}
                href="/login"
              >
                Get Started
              </Link>
            </div>

            {/* Mobile menu button */}
            <button 
              className="md:hidden"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              style={{ color: colors.primary }}
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Navigation */}
          {isMenuOpen && (
            <div className="md:hidden backdrop-blur-lg rounded-2xl shadow-xl mb-4 p-6 animate-in fade-in slide-in-from-top-4 duration-300" style={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
              <div className="flex flex-col space-y-4">
                <a href="#features" style={{ color: '#4b5563' }} className="hover:opacity-80 transition-opacity duration-300">Features</a>
                {/* <a href="#" style={{ color: '#4b5563' }} className="hover:opacity-80 transition-opacity duration-300">About</a> */}
                {/* <a href="#" style={{ color: '#4b5563' }} className="hover:opacity-80 transition-opacity duration-300">Contact</a> */}
                <Link 
                  className="px-6 py-3 rounded-full font-medium transition-all duration-300 hover:shadow-lg"
                  href="/login"
                >
                  Get Started
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div 
              className="inline-flex items-center space-x-2 backdrop-blur-sm border rounded-full px-4 py-2 text-sm font-medium mb-8 animate-in fade-in slide-in-from-top-6 duration-700"
              style={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.6)', 
                borderColor: colors.secondary,
                color: colors.primary 
              }}
            >
              <span 
                className="w-2 h-2 rounded-full animate-pulse" 
                style={{ backgroundColor: colors.primary }}
              ></span>
              <span>AI-Powered Healthcare Follow-up</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-5xl lg:text-7xl font-bold mb-6 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-200" style={{ color: '#111827' }}>
              AI that follows up,
              <span 
                className="block text-transparent bg-clip-text"
                style={{ 
                  backgroundImage: `linear-gradient(to right, ${colors.primary}, #074a61)`,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}
              >
                so you can focus on healing
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl mb-12 leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-700 delay-400" style={{ color: '#4b5563' }}>
              Transform patient care with intelligent follow-ups, automated report analysis, and seamless appointment management. 
              Let AI handle the routine, while you focus on what matters most.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-600">
              <Link 
                className="group px-8 py-4 rounded-full font-semibold transition-all duration-300 hover:shadow-xl hover:scale-105 flex items-center space-x-2"
                style={{ backgroundColor: colors.primary, color: colors.background }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#074a61'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = colors.primary}
                href="/login"
              >
                <span>Get Started</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
              </Link>
              <Link 
                className="group px-8 py-4 rounded-full font-semibold transition-all duration-300 hover:shadow-lg hover:scale-105 flex items-center space-x-2 backdrop-blur-sm border"
                style={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.8)',
                  borderColor: colors.secondary,
                  color: colors.primary 
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'white'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.8)'}
                href="/login"
                >
                <span>Try Now</span>
                <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
              </Link>
            </div>
          </div>

          {/* Hero Visual */}
          <div className="mt-20 relative animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-800">
            <div className="relative">
              {/* Main Dashboard Mockup */}
              <div 
                className="backdrop-blur-sm rounded-3xl shadow-2xl border p-8 max-w-4xl mx-auto"
                style={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.8)',
                  borderColor: `${colors.secondary}80`
                }}
              >
                <div className="flex items-center space-x-3 mb-6">
                  <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                </div>
                <div 
                  className="rounded-2xl p-6 h-96 flex items-center justify-center"
                  style={{ 
                    background: `linear-gradient(135deg, ${colors.background} 0%, ${colors.secondary}30 100%)`
                  }}
                >
                  <img src="/dashboard.png" alt="Dashboard" className="w-full h-full object-contain" />
                  {/* <div className="text-center">
                    <div 
                      className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                      style={{ background: `linear-gradient(135deg, ${colors.primary} 0%, #074a61 100%)` }}
                    >
                      <MessageSquare className="w-8 h-8" style={{ color: colors.background }} />
                    </div>
                    <h3 className="text-xl font-semibold mb-2" style={{ color: '#111827' }}>DocFollow Dashboard</h3>
                    <p style={{ color: '#4b5563' }}>Intelligent patient follow-up management</p>
                  </div> */}
                </div>
              </div>

              {/* Floating Elements */}
              <div 
                className="absolute -top-6 -left-6 w-24 h-24 rounded-2xl backdrop-blur-sm animate-bounce"
                style={{ 
                  background: `linear-gradient(135deg, ${colors.primary}20 0%, #074a6120 100%)`,
                  animationDelay: '1000ms'
                }}
              ></div>
              <div 
                className="absolute -bottom-6 -right-6 w-32 h-32 rounded-full backdrop-blur-sm animate-pulse"
                style={{ 
                  background: `linear-gradient(135deg, ${colors.secondary}40 0%, ${colors.primary}20 100%)`,
                  animationDelay: '1500ms'
                }}
              ></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl lg:text-5xl font-bold mb-6" style={{ color: '#111827' }}>
              Everything you need for
              <span 
                className="block text-transparent bg-clip-text"
                style={{ 
                  backgroundImage: `linear-gradient(to right, ${colors.primary}, #074a61)`,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}
              >
                seamless patient care
              </span>
            </h2>
            <p className="text-xl max-w-3xl mx-auto" style={{ color: '#4b5563' }}>
              Our comprehensive platform combines AI intelligence with human expertise to deliver exceptional patient follow-up experiences.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group backdrop-blur-sm border rounded-2xl p-8 hover:shadow-xl hover:scale-105 transition-all duration-500"
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.6)',
                  borderColor: `${colors.secondary}80`,
                  animationDelay: `${index * 200}ms`
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.8)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.6)'}
              >
                <div 
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6 group-hover:rotate-3 transition-transform duration-300"
                  style={{ background: `linear-gradient(135deg, ${colors.primary} 0%, #074a61 100%)` }}
                >
                  <feature.icon className="w-7 h-7" style={{ color: colors.background }} />
                </div>
                <h3 className="text-xl font-semibold mb-3" style={{ color: '#111827' }}>{feature.title}</h3>
                <p className="leading-relaxed" style={{ color: '#4b5563' }}>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div 
            className="rounded-3xl p-12 relative overflow-hidden"
            style={{ background: `linear-gradient(135deg, ${colors.primary} 0%, #074a61 100%)` }}
          >
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-4 right-4 w-32 h-32 border border-white rounded-full"></div>
              <div className="absolute bottom-4 left-4 w-24 h-24 border border-white rounded-full"></div>
            </div>

            <div className="relative">
              <h2 className="text-4xl lg:text-5xl font-bold mb-6" style={{ color: colors.background }}>
                Ready to transform your practice?
              </h2>
              <p className="text-xl mb-8 max-w-2xl mx-auto" style={{ color: `${colors.background}CC` }}>
                Join healthcare providers who are already using DocFollow to deliver exceptional patient care with AI-powered follow-ups.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link 
                  className="group px-8 py-4 rounded-full font-semibold transition-all duration-300 hover:shadow-xl hover:scale-105 flex items-center space-x-2"
                  style={{ backgroundColor: colors.background, color: colors.primary }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'white'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = colors.background}
                  href="/login"
                >
                  <span>Start Free</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
                </Link>
                <Link 
                  className="group bg-transparent border-2 px-8 py-4 rounded-full font-semibold transition-all duration-300"
                  style={{ 
                    borderColor: `${colors.background}4D`, 
                    color: colors.background 
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = colors.background;
                    e.currentTarget.style.backgroundColor = `${colors.background}1A`;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = `${colors.background}4D`;
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                  href="/login"
                >
                  Try Now
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 lg:px-8 border-t" style={{ borderColor: `${colors.secondary}80` }}>
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: colors.primary }}>
                <MessageSquare className="w-5 h-5" style={{ color: colors.background }} />
              </div>
              <span className="text-xl font-bold" style={{ color: colors.primary }}>DocFollow</span>
            </div>
            <div className="flex items-center space-x-6" style={{ color: '#4b5563' }}>
              <a 
                href="#" 
                className="transition-colors duration-300"
                onMouseEnter={(e) => e.currentTarget.style.color = colors.primary}
                onMouseLeave={(e) => e.currentTarget.style.color = '#4b5563'}
              >
                Privacy
              </a>
              <a 
                href="#" 
                className="transition-colors duration-300"
                onMouseEnter={(e) => e.currentTarget.style.color = colors.primary}
                onMouseLeave={(e) => e.currentTarget.style.color = '#4b5563'}
              >
                Terms
              </a>
              <a 
                href="#" 
                className="transition-colors duration-300"
                onMouseEnter={(e) => e.currentTarget.style.color = colors.primary}
                onMouseLeave={(e) => e.currentTarget.style.color = '#4b5563'}
              >
                Support
              </a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t text-center" style={{ borderColor: `${colors.secondary}80`, color: '#4b5563' }}>
            <p>&copy; 2025 DocFollow. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;