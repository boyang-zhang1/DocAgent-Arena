import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default async function DatasetsPage() {
  try {
    const datasets = await apiClient.getDatasets();

    return (
      <div>
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Available Datasets</h1>
          <p className="text-muted-foreground mt-2">
            Datasets used for RAG provider benchmarking
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {datasets.map((dataset) => (
            <Card key={dataset.name}>
              <CardHeader>
                <CardTitle>{dataset.display_name}</CardTitle>
                <CardDescription>{dataset.name}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">{dataset.description}</p>

                <div>
                  <p className="text-sm font-medium mb-2">Available Splits:</p>
                  <div className="flex flex-wrap gap-2">
                    {dataset.available_splits.map((split) => (
                      <Badge key={split} variant="outline">
                        {split}
                      </Badge>
                    ))}
                  </div>
                </div>

                {dataset.num_documents && (
                  <div>
                    <p className="text-sm font-medium">Documents:</p>
                    <p className="text-2xl font-bold">{dataset.num_documents.toLocaleString()}</p>
                  </div>
                )}

                <div>
                  <Badge>{dataset.task_type}</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Datasets</h2>
        <p className="text-muted-foreground">
          {error instanceof Error ? error.message : 'Failed to load datasets'}
        </p>
      </div>
    );
  }
}
