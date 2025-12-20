import type { ReactNode } from 'react'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { Footer } from './Footer'

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className="ml-64">
        <Header />
        {/* Main content area - Using spacing tokens */}
        <main className="pt-16 pb-3xl px-lg min-h-screen">{children}</main>
        <Footer />
      </div>
    </div>
  )
}
