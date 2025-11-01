import Link from 'next/link';

export function Navbar() {
  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo / Brand */}
          <Link href="/" className="text-2xl font-bold">
            RAGRace
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-6">
            <Link
              href="/"
              className="text-sm font-medium transition-colors hover:text-primary"
            >
              Results
            </Link>
            <Link
              href="/dashboard"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
            >
              Run Benchmark
            </Link>
            <Link
              href="/datasets"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
            >
              Datasets
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
