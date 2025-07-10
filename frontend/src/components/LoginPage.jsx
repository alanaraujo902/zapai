import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Brain, MessageSquare, Sparkles, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'

export default function LoginPage() {
  const { login, register } = useAuth()
  const { toggleTheme, isDark } = useTheme()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Estados do formulário de login
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  })

  // Estados do formulário de registro
  const [registerData, setRegisterData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: ''
  })

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const result = await login(loginData.email, loginData.password)
    
    if (!result.success) {
      setError(result.error)
    }
    
    setLoading(false)
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    // Validações
    if (registerData.password !== registerData.confirmPassword) {
      setError('As senhas não coincidem')
      setLoading(false)
      return
    }

    if (registerData.password.length < 8) {
      setError('A senha deve ter pelo menos 8 caracteres')
      setLoading(false)
      return
    }

    const result = await register(
      registerData.email,
      registerData.password,
      registerData.name,
      registerData.phone
    )
    
    if (!result.success) {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-8 items-center">
        
        {/* Seção de Apresentação */}
        <div className="space-y-8 text-center lg:text-left">
          <div className="space-y-4">
            <div className="flex items-center justify-center lg:justify-start gap-3">
              <div className="p-3 bg-primary rounded-xl">
                <Brain className="h-8 w-8 text-primary-foreground" />
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
                Anotações IA
              </h1>
            </div>
            
            <p className="text-xl text-muted-foreground max-w-lg">
              Organize seus pensamentos com inteligência artificial. 
              Capture ideias via WhatsApp e deixe a IA organizar tudo para você.
            </p>
          </div>

          {/* Features */}
          <div className="grid gap-6 max-w-lg mx-auto lg:mx-0">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <MessageSquare className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold">Integração WhatsApp</h3>
                <p className="text-sm text-muted-foreground">
                  Envie suas anotações diretamente pelo WhatsApp
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Sparkles className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h3 className="font-semibold">IA Inteligente</h3>
                <p className="text-sm text-muted-foreground">
                  Categorização automática e insights personalizados
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <Brain className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h3 className="font-semibold">Interface Obsidian</h3>
                <p className="text-sm text-muted-foreground">
                  Organização visual inspirada no Obsidian
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Seção de Login/Registro */}
        <div className="w-full max-w-md mx-auto">
          <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
            <CardHeader className="space-y-1 text-center">
              <div className="flex justify-between items-center">
                <CardTitle className="text-2xl">Bem-vindo</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleTheme}
                  className="h-8 w-8 p-0"
                >
                  {isDark ? '☀️' : '🌙'}
                </Button>
              </div>
              <CardDescription>
                Entre na sua conta ou crie uma nova
              </CardDescription>
            </CardHeader>

            <CardContent>
              <Tabs defaultValue="login" className="space-y-4">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="login">Entrar</TabsTrigger>
                  <TabsTrigger value="register">Registrar</TabsTrigger>
                </TabsList>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {/* Tab de Login */}
                <TabsContent value="login">
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-email">Email</Label>
                      <Input
                        id="login-email"
                        type="email"
                        placeholder="seu@email.com"
                        value={loginData.email}
                        onChange={(e) => setLoginData(prev => ({ ...prev, email: e.target.value }))}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="login-password">Senha</Label>
                      <div className="relative">
                        <Input
                          id="login-password"
                          type={showPassword ? "text" : "password"}
                          placeholder="Sua senha"
                          value={loginData.password}
                          onChange={(e) => setLoginData(prev => ({ ...prev, password: e.target.value }))}
                          required
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <Button type="submit" className="w-full" disabled={loading}>
                      {loading ? 'Entrando...' : 'Entrar'}
                    </Button>
                  </form>
                </TabsContent>

                {/* Tab de Registro */}
                <TabsContent value="register">
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-name">Nome</Label>
                      <Input
                        id="register-name"
                        type="text"
                        placeholder="Seu nome completo"
                        value={registerData.name}
                        onChange={(e) => setRegisterData(prev => ({ ...prev, name: e.target.value }))}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-email">Email</Label>
                      <Input
                        id="register-email"
                        type="email"
                        placeholder="seu@email.com"
                        value={registerData.email}
                        onChange={(e) => setRegisterData(prev => ({ ...prev, email: e.target.value }))}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-phone">WhatsApp (opcional)</Label>
                      <Input
                        id="register-phone"
                        type="tel"
                        placeholder="+55 11 99999-9999"
                        value={registerData.phone}
                        onChange={(e) => setRegisterData(prev => ({ ...prev, phone: e.target.value }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-password">Senha</Label>
                      <div className="relative">
                        <Input
                          id="register-password"
                          type={showPassword ? "text" : "password"}
                          placeholder="Mínimo 8 caracteres"
                          value={registerData.password}
                          onChange={(e) => setRegisterData(prev => ({ ...prev, password: e.target.value }))}
                          required
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-confirm">Confirmar Senha</Label>
                      <Input
                        id="register-confirm"
                        type="password"
                        placeholder="Confirme sua senha"
                        value={registerData.confirmPassword}
                        onChange={(e) => setRegisterData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                        required
                      />
                    </div>

                    <Button type="submit" className="w-full" disabled={loading}>
                      {loading ? 'Criando conta...' : 'Criar conta'}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

