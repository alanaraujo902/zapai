import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { 
  User, 
  MessageSquare, 
  Brain, 
  Bell, 
  Shield,
  Palette,
  Save,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'

export default function SettingsPage() {
  const { user } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [settings, setSettings] = useState({
    whatsappOptIn: true,
    aiProcessing: true,
    dailySummary: true,
    notifications: true,
    darkMode: theme === 'dark'
  })

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    if (key === 'darkMode') {
      toggleTheme()
    }
  }

  const handleSave = () => {
    console.log('Salvando configurações:', settings)
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Configurações</h1>
        <p className="text-muted-foreground">
          Gerencie suas preferências e configurações da conta
        </p>
      </div>

      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Perfil
          </CardTitle>
          <CardDescription>
            Informações da sua conta
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nome</Label>
              <Input id="name" defaultValue={user?.name} />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" defaultValue={user?.email} disabled />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="phone">WhatsApp</Label>
              <Input id="phone" type="tel" defaultValue={user?.phone_number} />
            </div>
            
            <div className="space-y-2">
              <Label>Status da Conta</Label>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="gap-1">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  Ativa
                </Badge>
                <Badge variant="secondary">
                  Plano Gratuito
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* WhatsApp Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            WhatsApp
          </CardTitle>
          <CardDescription>
            Configurações de integração com WhatsApp
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Receber anotações via WhatsApp</Label>
              <p className="text-sm text-muted-foreground">
                Permite enviar anotações diretamente pelo WhatsApp
              </p>
            </div>
            <Switch
              checked={settings.whatsappOptIn}
              onCheckedChange={(checked) => handleSettingChange('whatsappOptIn', checked)}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Notificações no WhatsApp</Label>
              <p className="text-sm text-muted-foreground">
                Receber confirmações e insights via WhatsApp
              </p>
            </div>
            <Switch
              checked={settings.notifications}
              onCheckedChange={(checked) => handleSettingChange('notifications', checked)}
            />
          </div>

          <div className="p-3 bg-muted rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="text-sm font-medium">WhatsApp Conectado</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Número: {user?.phone_number || 'Não configurado'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* AI Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Inteligência Artificial
          </CardTitle>
          <CardDescription>
            Configurações de processamento com IA
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Processamento automático</Label>
              <p className="text-sm text-muted-foreground">
                Processar anotações automaticamente com IA
              </p>
            </div>
            <Switch
              checked={settings.aiProcessing}
              onCheckedChange={(checked) => handleSettingChange('aiProcessing', checked)}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Resumo diário</Label>
              <p className="text-sm text-muted-foreground">
                Gerar resumo diário das anotações
              </p>
            </div>
            <Switch
              checked={settings.dailySummary}
              onCheckedChange={(checked) => handleSettingChange('dailySummary', checked)}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-3 bg-muted rounded-lg">
            <div>
              <div className="text-sm font-medium">Uso de IA hoje</div>
              <div className="text-xs text-muted-foreground">ChatGPT: 5 | Perplexity: 2</div>
            </div>
            <div>
              <div className="text-sm font-medium">Limite mensal</div>
              <div className="text-xs text-muted-foreground">100 processamentos</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Appearance Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Aparência
          </CardTitle>
          <CardDescription>
            Personalize a interface do aplicativo
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Modo escuro</Label>
              <p className="text-sm text-muted-foreground">
                Usar tema escuro na interface
              </p>
            </div>
            <Switch
              checked={settings.darkMode}
              onCheckedChange={(checked) => handleSettingChange('darkMode', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Segurança
          </CardTitle>
          <CardDescription>
            Configurações de segurança da conta
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline">
              Alterar Senha
            </Button>
            <Button variant="outline">
              Sessões Ativas
            </Button>
          </div>
          
          <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
              <span className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Dados Sensíveis
              </span>
            </div>
            <p className="text-xs text-yellow-700 dark:text-yellow-300">
              Suas anotações são processadas por APIs externas (ChatGPT, Perplexity). 
              Evite incluir informações muito sensíveis.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} className="gap-2">
          <Save className="h-4 w-4" />
          Salvar Configurações
        </Button>
      </div>
    </div>
  )
}

