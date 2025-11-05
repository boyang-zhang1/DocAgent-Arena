import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default async function DatasetsPage() {
  let datasets: Awaited<ReturnType<typeof apiClient.getDatasets>> | null = null;
  let fetchError: unknown = null;

  try {
    datasets = await apiClient.getDatasets();
  } catch (error) {
    fetchError = error;
  }

  if (!datasets) {
    const message = fetchError instanceof Error ? fetchError.message : 'Failed to load datasets';

    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Datasets</h2>
        <p className="text-muted-foreground">{message}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Datasets</h1>
        <p className="text-muted-foreground mt-2">
          Available datasets for RAG benchmarking
        </p>
      </div>

      <div className="space-y-8">
        {datasets.map((dataset) => (
          <Link key={dataset.name} href={`/datasets/${dataset.name}`}>
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
              {/* Dataset Header */}
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-2xl hover:text-primary transition-colors">
                      {dataset.display_name}
                    </CardTitle>
                    <CardDescription className="mt-1">{dataset.description}</CardDescription>
                  </div>
                  <Badge variant="outline" className="ml-4">
                    {dataset.task_type}
                  </Badge>
                </div>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
