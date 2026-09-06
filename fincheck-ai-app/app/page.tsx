'use client';
// app/page.tsx — Login Page
import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Check, Lock, Shield } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    router.prefetch('/dashboard');
  }, [router]);

  const handleSignIn = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      router.push('/dashboard');
      setTimeout(() => {
        if (window.location.pathname !== '/dashboard') {
          window.location.href = '/dashboard';
        }
      }, 400);
    }, 300);
  };

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: '#f0f2f7' }}>
      {/* ── Left Panel ── */}
      <div
        className="w-[440px] md:w-[480px] lg:w-[520px] xl:w-[580px] flex-shrink-0 flex flex-col justify-between px-10 lg:px-14 py-10 relative overflow-hidden"
        style={{ backgroundColor: '#0f1629' }}
      >
        {/* Subtle background gradient accents */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none -ml-20 -mb-20" />

        {/* Top: Logo */}
        <div className="relative z-10">
          <div className="flex items-center gap-3.5 mb-14">
            <div className="w-12 h-12 rounded-full overflow-hidden flex items-center justify-center shadow-xl shadow-blue-500/20 ring-1 ring-white/15 flex-shrink-0">
              <Image
                src="/logo.png"
                alt="FinCheck AI"
                width={48}
                height={48}
                className="w-full h-full object-cover"
                priority
              />
            </div>
            <div>
              <div className="text-white font-semibold text-lg leading-tight">FinCheck AI</div>
              <div className="text-[10px] font-medium tracking-widest text-slate-400 uppercase mt-0.5">
                RETRIEVE. VERIFY. ADVISE.
              </div>
            </div>
          </div>

          {/* Headline */}
          <div className="mb-10">
            <h2 className="text-3xl lg:text-4xl font-bold text-white leading-tight mb-5 tracking-tight">
              AI-powered financial
              <br />
              knowledge at your fingertips
            </h2>
            <p className="text-slate-300 text-sm lg:text-[15px] leading-relaxed max-w-[440px]">
              Access approved investment policies, tax rules, product brochures, and compliance
              guidelines instantly with full audit trail citations.
            </p>
          </div>

          {/* Feature bullets */}
          <ul className="space-y-4">
            {[
              {
                title: 'Grounded in approved bank documents',
                desc: 'Only indexed against certified internal repositories',
              },
              {
                title: 'Every answer shows its source',
                desc: 'Clickable paragraph-level citations with doc codes',
              },
              {
                title: 'Compliant with internal standards',
                desc: 'Adheres to Wealth Division governance & disclaimers',
              },
            ].map((feature) => (
              <li key={feature.title} className="flex items-start gap-3.5">
                <div className="w-5 h-5 rounded-full bg-blue-500/20 border border-blue-400/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Check size={12} className="text-blue-400" />
                </div>
                <div>
                  <div className="text-white text-sm font-medium">{feature.title}</div>
                  <div className="text-slate-400 text-xs mt-0.5">{feature.desc}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Footer */}
        <div className="relative z-10 mt-12">
          <div className="border-t border-white/10 pt-6">
            <p className="text-slate-400 text-xs leading-relaxed mb-2">
              For authorised bank personnel only. All activity is logged and monitored in accordance
              with internal security policies.
            </p>
            <p className="text-slate-500 text-[11px]">
              © 2026 Wealth Division · Internal Use Only · FinCheck Core v2.4
            </p>
          </div>
        </div>
      </div>

      {/* ── Right Panel ── */}
      <div className="flex-1 flex items-center justify-center bg-white px-8">
        <div className="w-full max-w-[380px]">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-1.5">Welcome to FinCheck AI</h1>
            <p className="text-sm text-gray-500">Your trusted financial knowledge assistant</p>
          </div>

          <form onSubmit={handleSignIn} className="space-y-5">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
                Work Email
              </label>
              <input
                id="email"
                type="email"
                defaultValue="isha.rode@bankname.com"
                className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                placeholder="isha.rode@bankname.com"
                required
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  defaultValue="••••••••••"
                  className="w-full px-3.5 py-2.5 text-sm border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors pr-10"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Remember me + Forgot */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <div className="relative">
                  <input
                    type="checkbox"
                    id="remember-me"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-3.5 h-3.5 border border-gray-300 rounded accent-blue-600"
                  />
                </div>
                <span className="text-sm text-gray-600">Remember me</span>
              </label>
              <button
                type="button"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                Forgot password?
              </button>
            </div>

            {/* Sign In button */}
            <button
              id="sign-in-btn"
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 rounded-lg text-sm font-semibold text-white transition-all disabled:opacity-70"
              style={{ backgroundColor: '#0f1629' }}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Security note */}
          <div className="mt-6 text-center space-y-1.5">
            <div className="flex items-center justify-center gap-1.5 text-gray-400 text-xs">
              <Lock size={11} />
              <span>
                Secured with enterprise-grade encryption. All sessions are monitored for compliance.
              </span>
            </div>
            <p className="text-xs text-gray-400">
              For technical support, contact{' '}
              <a
                href="mailto:it-helpdesk@bankname.com"
                className="text-blue-500 hover:underline"
              >
                it-helpdesk@bankname.com
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
