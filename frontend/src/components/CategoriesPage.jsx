import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { FolderOpen, Plus, MoreVertical, FileText } from 'lucide-react'

export default function CategoriesPage() {
  const categories = [
    { id: 1, name: 'Trabalho', count: 15, color: 'bg-blue-500', description: 'Anotações relacionadas ao trabalho' },
    { id: 2, name: 'Pessoal', count: 8, color: 'bg-green-500', description: 'Anotações pessoais e familiares' },
    { id: 3, name: 'Ideias', count: 12, color: 'bg-purple-500', description: 'Ideias e inspirações' },
    { id: 4, name: 'Projetos', count: 6, color: 'bg-orange-500', description: 'Projetos em andamento' },
    { id: 5, name: 'Estudos', count: 9, color: 'bg-red-500', description: 'Material de estudo e aprendizado' }
  ]

  return (
    <div className="p-6 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Categorias</h1>
          <p className="text-muted-foreground">
            Organize suas anotações por categorias
          </p>
        </div>
        
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Nova Categoria
        </Button>
      </div>

      {/* Categories Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map((category) => (
          <Card key={category.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${category.color}`}>
                    <FolderOpen className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{category.name}</CardTitle>
                    <CardDescription>{category.description}</CardDescription>
                  </div>
                </div>
                
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    {category.count} anotações
                  </span>
                </div>
                
                <Badge variant="secondary">
                  {category.count}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {/* Add New Category Card */}
        <Card className="border-dashed border-2 hover:border-primary transition-colors cursor-pointer">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="p-3 bg-muted rounded-lg mb-3">
              <Plus className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="font-medium mb-1">Nova Categoria</h3>
            <p className="text-sm text-muted-foreground text-center">
              Clique para criar uma nova categoria
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

