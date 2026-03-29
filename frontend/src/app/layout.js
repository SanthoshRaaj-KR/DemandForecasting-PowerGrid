import './globals.css'
import { NavBar } from '@/components/ui/NavBar'

export const metadata = {
  title: 'India Grid Digital Twin',
  description: 'LightGBM + LLM Agentic Smart Grid Simulation',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="scanline">
        <NavBar />
        <main className="min-h-screen">
          {children}
        </main>
      </body>
    </html>
  )
}
