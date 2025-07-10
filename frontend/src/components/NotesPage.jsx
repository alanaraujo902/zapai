import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { 
  FileText, 
  Search, 
  Filter,
  Plus,
  Brain,
  Calendar,
  Tag,
  MoreVertical
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

export default function NotesPage() {
  const { apiRequest } = useAuth()
  const [notes, setNotes] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')

  useEffect(() => {
    loadNotes()
  }, [])

  const loadNotes = async () => {
    try {
      const response = await apiRequest('/notes')
      setNotes(response.notes || [])
    } catch (error) {
      console.error('Erro ao carregar anotações:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredNotes = notes.filter(note => {
    const matchesSearch = note.content?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         note.title?.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || note.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const getStatusColor = (status) => {
    switch (status) {
      case 'processed': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
      case 'processing': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
      case 'pending': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'processed': return 'Processada'
      case 'processing': return 'Processando'
      case 'pending': return 'Pendente'
      case 'failed': return 'Falha'
      default: return 'Desconhecido'
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3"></div>
          <div className="grid gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-32 bg-muted rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Anotações</h1>
          <p className="text-muted-foreground">
            Gerencie e organize suas anotações
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Nova Anotação
          </Button>
          <Button variant="outline" className="gap-2">
            <Brain className="h-4 w-4" />
            Processar IA
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar anotações..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="gap-2">
                <Filter className="h-4 w-4" />
                Filtros
              </Button>
              
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-2 border border-input bg-background rounded-md text-sm"
              >
                <option value="all">Todas as categorias</option>
                <option value="trabalho">Trabalho</option>
                <option value="pessoal">Pessoal</option>
                <option value="ideias">Ideias</option>
                <option value="projetos">Projetos</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notes Grid */}
      <div className="grid gap-4">
        {filteredNotes.length > 0 ? (
          filteredNotes.map((note) => (
            <Card key={note.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-lg truncate">
                      {note.title || note.content?.substring(0, 60) + '...'}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2 mt-1">
                      <Calendar className="h-3 w-3" />
                      {new Date(note.created_at).toLocaleDateString('pt-BR')}
                      {note.source && (
                        <>
                          <span>•</span>
                          <span className="capitalize">{note.source}</span>
                        </>
                      )}
                    </CardDescription>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Badge className={getStatusColor(note.status)}>
                      {getStatusText(note.status)}
                    </Badge>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {note.content}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {note.category && (
                        <Badge variant="secondary" className="gap-1">
                          <Tag className="h-3 w-3" />
                          {note.category}
                        </Badge>
                      )}
                      
                      {note.tags && note.tags.length > 0 && (
                        <div className="flex gap-1">
                          {note.tags.slice(0, 3).map((tag, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                          {note.tags.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{note.tags.length - 3}
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-1">
                      {note.insights_count > 0 && (
                        <Badge variant="outline" className="gap-1">
                          <Brain className="h-3 w-3" />
                          {note.insights_count}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <h3 className="text-lg font-medium mb-2">Nenhuma anotação encontrada</h3>
                <p className="text-muted-foreground mb-4">
                  {searchQuery || selectedCategory !== 'all' 
                    ? 'Tente ajustar os filtros de busca'
                    : 'Comece criando sua primeira anotação'
                  }
                </p>
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  Nova Anotação
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

