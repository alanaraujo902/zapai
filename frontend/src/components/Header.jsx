import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { 
  Menu,
  Search,
  Bell,
  Plus,
  Brain,
  MessageSquare,
  User,
  Settings,
  LogOut,
  Sun,
  Moon
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'

export default function Header({ onMenuClick }) {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [searchQuery, setSearchQuery] = useState('')
  const [notifications] = useState([
    { id: 1, message: 'Nova anotação processada pela IA', time: '2 min' },
    { id: 2, message: 'Resumo diário disponível', time: '1h' },
    { id: 3, message: 'WhatsApp conectado com sucesso', time: '3h' }
  ])

  const handleSearch = (e) => {
    e.preventDefault()
    console.log('Buscar:', searchQuery)
  }

  const handleNewNote = () => {
    console.log('Nova anotação')
  }

  const handleProcessAI = () => {
    console.log('Processar com IA')
  }

  return (
    <header className="h-16 bg-background border-b border-border flex items-center justify-between px-6">
      
      {/* Left Section */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
          className="lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Search */}
        <form onSubmit={handleSearch} className="hidden md:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Buscar anotações, categorias..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-80 bg-muted/50"
            />
          </div>
        </form>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-3">
        
        {/* Quick Actions */}
        <div className="hidden sm:flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewNote}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            Nova
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleProcessAI}
            className="gap-2"
          >
            <Brain className="h-4 w-4" />
            IA
          </Button>
        </div>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleTheme}
          className="h-9 w-9 p-0"
        >
          {theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-9 w-9 p-0 relative">
              <Bell className="h-4 w-4" />
              {notifications.length > 0 && (
                <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0 text-xs">
                  {notifications.length}
                </Badge>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Notificações</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {notifications.length > 0 ? (
              notifications.map((notification) => (
                <DropdownMenuItem key={notification.id} className="flex flex-col items-start p-3">
                  <div className="text-sm">{notification.message}</div>
                  <div className="text-xs text-muted-foreground">{notification.time} atrás</div>
                </DropdownMenuItem>
              ))
            ) : (
              <DropdownMenuItem disabled>
                Nenhuma notificação
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* WhatsApp Status */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900/30 rounded-full">
          <MessageSquare className="h-3 w-3 text-green-600 dark:text-green-400" />
          <span className="text-xs text-green-700 dark:text-green-300">WhatsApp</span>
          <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
        </div>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-9 w-9 p-0 rounded-full">
              <Avatar className="h-8 w-8">
                <AvatarImage src={user?.avatar} alt={user?.name} />
                <AvatarFallback>
                  {user?.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              Perfil
            </DropdownMenuItem>
            
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              Configurações
            </DropdownMenuItem>
            
            <DropdownMenuSeparator />
            
            <DropdownMenuItem onClick={logout} className="text-red-600 dark:text-red-400">
              <LogOut className="mr-2 h-4 w-4" />
              Sair
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}

