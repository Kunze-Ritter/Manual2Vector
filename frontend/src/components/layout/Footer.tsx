import { Button } from '@/components/ui/button'
import { Book, Code, HelpCircle } from 'lucide-react'

export function Footer() {
  return (
    <footer className="fixed bottom-0 left-64 right-0 h-12 bg-card border-t border-border">
      <div className="flex items-center justify-between h-full px-6">
        {/* Left Section */}
        <div className="text-sm text-muted-foreground">© 2025 KRAI Dashboard. All rights reserved.</div>

        {/* Right Section */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild>
            <a href="#" className="flex items-center gap-1">
              <Book className="h-4 w-4" />
              <span className="hidden sm:inline text-xs">Docs</span>
            </a>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <a href="#" className="flex items-center gap-1">
              <Code className="h-4 w-4" />
              <span className="hidden sm:inline text-xs">API</span>
            </a>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <a href="#" className="flex items-center gap-1">
              <HelpCircle className="h-4 w-4" />
              <span className="hidden sm:inline text-xs">Support</span>
            </a>
          </Button>
        </div>
      </div>
    </footer>
  )
}
