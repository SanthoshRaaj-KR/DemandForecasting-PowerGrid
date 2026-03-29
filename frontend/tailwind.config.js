/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,jsx}',
    './src/components/**/*.{js,jsx}',
    './src/app/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['var(--font-display)', 'sans-serif'],
        body: ['var(--font-body)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      colors: {
        grid: {
          bg: '#070a0f',
          surface: '#0d1117',
          card: '#111827',
          border: '#1e2d3d',
          cyan: '#00d4ff',
          blue: '#0066ff',
          amber: '#f59e0b',
          red: '#ef4444',
          green: '#10b981',
          purple: '#8b5cf6',
          muted: '#4b5563',
          text: '#e2e8f0',
          textDim: '#94a3b8',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flow': 'flow 2s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan': 'scan 4s linear infinite',
      },
      keyframes: {
        flow: {
          '0%': { strokeDashoffset: '100' },
          '100%': { strokeDashoffset: '0' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px #00d4ff33, 0 0 10px #00d4ff22' },
          '100%': { boxShadow: '0 0 20px #00d4ff66, 0 0 40px #00d4ff33' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        }
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
