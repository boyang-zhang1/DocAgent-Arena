-- CreateEnum
CREATE TYPE "BattleRunStatus" AS ENUM ('SUCCESS', 'ERROR');

-- CreateTable
CREATE TABLE "parse_battle_runs" (
    "id" TEXT NOT NULL,
    "upload_file_id" TEXT NOT NULL,
    "original_name" TEXT,
    "storage_path" TEXT NOT NULL,
    "storage_url" TEXT,
    "page_number" INTEGER NOT NULL,
    "providers" TEXT[],
    "status" "BattleRunStatus" NOT NULL,
    "page_credits" DOUBLE PRECISION,
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "started_at" TIMESTAMP(3),
    "completed_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "parse_battle_runs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "battle_provider_results" (
    "id" TEXT NOT NULL,
    "battle_id" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "content" JSONB NOT NULL DEFAULT '{}',
    "total_pages" INTEGER NOT NULL,
    "usage" JSONB NOT NULL DEFAULT '{}',
    "cost_credits" DOUBLE PRECISION,
    "cost_usd" DOUBLE PRECISION,
    "processing_time" DOUBLE PRECISION,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "battle_provider_results_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "battle_feedback" (
    "id" TEXT NOT NULL,
    "battle_id" TEXT NOT NULL,
    "preferred_labels" TEXT[],
    "comment" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "revealed_at" TIMESTAMP(3),

    CONSTRAINT "battle_feedback_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "parse_battle_runs_status_idx" ON "parse_battle_runs"("status");

-- CreateIndex
CREATE INDEX "battle_provider_results_battle_id_idx" ON "battle_provider_results"("battle_id");

-- CreateIndex
CREATE UNIQUE INDEX "battle_feedback_battle_id_key" ON "battle_feedback"("battle_id");

-- AddForeignKey
ALTER TABLE "battle_provider_results" ADD CONSTRAINT "battle_provider_results_battle_id_fkey" FOREIGN KEY ("battle_id") REFERENCES "parse_battle_runs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "battle_feedback" ADD CONSTRAINT "battle_feedback_battle_id_fkey" FOREIGN KEY ("battle_id") REFERENCES "parse_battle_runs"("id") ON DELETE CASCADE ON UPDATE CASCADE;
