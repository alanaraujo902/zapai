import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Home, 
  FileText, 
  FolderOpen, 
  Settings, 
  Brain,
  MessageSquare,
  Plus,
  Search,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { cn } from '@/lib/utils'

export default function Sidebar({ isOpen, onToggle }) {
  const location = useLocation()
  const [searchQuery, setSearchQuery] = useState('')

  const menuItems = [
    {
      title: 'Dashboard',
      icon: Home,
      path: '/dashboard',
      badge: null
    },
    {
      title: 'Anotações',
      icon: FileText,
      path: '/notes',
      badge: '12'
    },
    {
      title: 'Categorias',
      icon: FolderOpen,
      path: '/categories',
      badge: null
    },
    {
      title: 'Configurações',
      icon: Settings,
      path: '/settings',
      badge: null
    }
  ]

  const quickActions = [
    {
      title: 'Nova Anotação',
      icon: Plus,
      action: () => console.log('Nova anotação')
    },
    {
      title: 'Processar IA',
      icon: Brain,
      action: () => console.log('Processar IA')
    },
    {
      title: 'WhatsApp',
      icon: MessageSquare,
      action: () => console.log('WhatsApp')
    }
  ]

  const recentCategories = [
    { name: 'Trabalho', count: 5, color: 'bg-blue-500' },
    { name: 'Ideias', count: 3, color: 'bg-purple-500' },
    { name: 'Projetos', count: 8, color: 'bg-green-500' },
    { name: 'Pessoal', count: 2, color: 'bg-orange-500' }
  ]

  return (
    <div className={cn(
      "fixed left-0 top-0 h-full bg-sidebar border-r border-sidebar-border transition-all duration-300 z-50",
      isOpen ? "w-64" : "w-16"
    )}>
      <div className="flex flex-col h-full">
        
        {/* Header */}
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center justify-between">
            {isOpen && (
              <div className="flex items-center gap-2">
                <div className="p-2 bg-primary rounded-lg">
                  <Brain className="h-5 w-5 text-primary-foreground" />
                </div>
                <span className="font-semibold text-sidebar-foreground">Anotações IA</span>
              </div>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              className="h-8 w-8 p-0 hover:bg-sidebar-accent"
            >
              {isOpen ? (
                <ChevronLeft className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Search */}
        {isOpen && (
          <div className="p-4 border-b border-sidebar-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Buscar anotações..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-sidebar-accent rounded-lg border-0 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto">
          <nav className="p-2">
            
            {/* Main Menu */}
            <div className="space-y-1">
              {menuItems.map((item) => {
                const isActive = location.pathname === item.path
                const Icon = item.icon
                
                return (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant={isActive ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 h-10",
                        !isOpen && "justify-center px-2",
                        isActive && "bg-sidebar-accent text-sidebar-accent-foreground"
                      )}
                    >
                      <Icon className="h-4 w-4 flex-shrink-0" />
                      {isOpen && (
                        <>
                          <span className="flex-1 text-left">{item.title}</span>
                          {item.badge && (
                            <Badge variant="secondary" className="ml-auto">
                              {item.badge}
                            </Badge>
                          )}
                        </>
                      )}
                    </Button>
                  </Link>
                )
              })}
            </div>

            {/* Quick Actions */}
            {isOpen && (
              <div className="mt-6">
                <h3 className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Ações Rápidas
                </h3>
                <div className="space-y-1">
                  {quickActions.map((action) => {
                    const Icon = action.icon
                    
                    return (
                      <Button
                        key={action.title}
                        variant="ghost"
                        onClick={action.action}
                        className="w-full justify-start gap-3 h-9"
                      >
                        <Icon className="h-4 w-4" />
                        <span>{action.title}</span>
                      </Button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Recent Categories */}
            {isOpen && (
              <div className="mt-6">
                <h3 className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Categorias Recentes
                </h3>
                <div className="space-y-1">
                  {recentCategories.map((category) => (
                    <Button
                      key={category.name}
                      variant="ghost"
                      className="w-full justify-start gap-3 h-9"
                    >
                      <div className={cn("h-3 w-3 rounded-full", category.color)} />
                      <span className="flex-1 text-left">{category.name}</span>
                      <Badge variant="outline" className="ml-auto">
                        {category.count}
                      </Badge>
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </nav>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-sidebar-border">
          {isOpen ? (
            <div className="text-xs text-muted-foreground text-center">
              <p>Anotações IA v1.0</p>
              <p>Powered by ChatGPT & Perplexity</p>
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="h-2 w-2 bg-green-500 rounded-full" />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

