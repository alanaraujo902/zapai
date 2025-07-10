import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  FileText, 
  Brain, 
  MessageSquare, 
  TrendingUp,
  Clock,
  Target,
  Sparkles,
  Plus,
  ArrowRight,
  Calendar,
  BarChart3
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

export default function Dashboard() {
  const { user, apiRequest } = useAuth()
  const [stats, setStats] = useState({
    totalNotes: 0,
    processedNotes: 0,
    pendingNotes: 0,
    totalInsights: 0,
    apiUsageToday: { chatgpt: 0, perplexity: 0 }
  })
  const [recentNotes, setRecentNotes] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      // Carrega estatísticas de IA
      const statsResponse = await apiRequest('/ai/stats')
      setStats(statsResponse)

      // Carrega anotações recentes
      const notesResponse = await apiRequest('/notes?limit=5&sort=created_at&order=desc')
      setRecentNotes(notesResponse.notes || [])
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const processingProgress = stats.totalNotes > 0 
    ? (stats.processedNotes / stats.totalNotes) * 100 
    : 0

  const quickActions = [
    {
      title: 'Nova Anotação',
      description: 'Criar uma nova anotação',
      icon: Plus,
      action: () => console.log('Nova anotação'),
      color: 'bg-blue-500'
    },
    {
      title: 'Processar IA',
      description: 'Processar anotações pendentes',
      icon: Brain,
      action: () => console.log('Processar IA'),
      color: 'bg-purple-500'
    },
    {
      title: 'Resumo Diário',
      description: 'Gerar resumo do dia',
      icon: Calendar,
      action: () => console.log('Resumo diário'),
      color: 'bg-green-500'
    }
  ]

  const insights = [
    {
      title: 'Produtividade em Alta',
      description: 'Você criou 40% mais anotações esta semana',
      icon: TrendingUp,
      color: 'text-green-600'
    },
    {
      title: 'Categoria Popular',
      description: 'Trabalho é sua categoria mais usada',
      icon: Target,
      color: 'text-blue-600'
    },
    {
      title: 'IA Ativa',
      description: '15 insights gerados hoje',
      icon: Sparkles,
      color: 'text-purple-600'
    }
  ]

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
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
          <h1 className="text-3xl font-bold">Olá, {user?.name?.split(' ')[0]}! 👋</h1>
          <p className="text-muted-foreground">
            Aqui está um resumo das suas anotações e insights
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <MessageSquare className="h-3 w-3" />
            WhatsApp Conectado
          </Badge>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Anotações</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalNotes}</div>
            <p className="text-xs text-muted-foreground">
              {stats.pendingNotes} pendentes
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processadas por IA</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.processedNotes}</div>
            <div className="mt-2">
              <Progress value={processingProgress} className="h-2" />
              <p className="text-xs text-muted-foreground mt-1">
                {processingProgress.toFixed(0)}% processadas
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Insights Gerados</CardTitle>
            <Sparkles className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalInsights}</div>
            <p className="text-xs text-muted-foreground">
              Pela inteligência artificial
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uso de IA Hoje</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.apiUsageToday.chatgpt + stats.apiUsageToday.perplexity}
            </div>
            <p className="text-xs text-muted-foreground">
              ChatGPT: {stats.apiUsageToday.chatgpt} | Perplexity: {stats.apiUsageToday.perplexity}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Ações Rápidas</CardTitle>
          <CardDescription>
            Acesse rapidamente as funcionalidades principais
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {quickActions.map((action) => {
              const Icon = action.icon
              return (
                <Button
                  key={action.title}
                  variant="outline"
                  onClick={action.action}
                  className="h-auto p-4 flex flex-col items-start gap-2 hover:bg-muted/50"
                >
                  <div className={`p-2 rounded-lg ${action.color}`}>
                    <Icon className="h-4 w-4 text-white" />
                  </div>
                  <div className="text-left">
                    <div className="font-medium">{action.title}</div>
                    <div className="text-xs text-muted-foreground">{action.description}</div>
                  </div>
                </Button>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Recent Notes */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Anotações Recentes</CardTitle>
              <CardDescription>Suas últimas anotações</CardDescription>
            </div>
            <Button variant="ghost" size="sm">
              Ver todas
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentNotes.length > 0 ? (
                recentNotes.map((note) => (
                  <div key={note.id} className="flex items-start gap-3 p-3 rounded-lg border">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">
                        {note.title || note.content?.substring(0, 50) + '...'}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {note.category && (
                          <Badge variant="secondary" className="mr-2">
                            {note.category}
                          </Badge>
                        )}
                        <Clock className="inline h-3 w-3 mr-1" />
                        {new Date(note.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <Badge variant={note.status === 'processed' ? 'default' : 'secondary'}>
                      {note.status === 'processed' ? 'Processada' : 'Pendente'}
                    </Badge>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Nenhuma anotação ainda</p>
                  <p className="text-sm">Comece criando sua primeira anotação</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Insights */}
        <Card>
          <CardHeader>
            <CardTitle>Insights da IA</CardTitle>
            <CardDescription>Descobertas sobre seus padrões</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {insights.map((insight, index) => {
                const Icon = insight.icon
                return (
                  <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                    <Icon className={`h-5 w-5 mt-0.5 ${insight.color}`} />
                    <div className="flex-1">
                      <div className="font-medium">{insight.title}</div>
                      <div className="text-sm text-muted-foreground">{insight.description}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

