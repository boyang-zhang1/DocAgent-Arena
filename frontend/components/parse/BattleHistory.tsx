"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { History, ChevronLeft, ChevronRight, Trophy, Minus, Users } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { BattleHistoryResponse, BattleHistoryItem } from "@/types/api";

export function BattleHistory() {
  const router = useRouter();
  const [history, setHistory] = useState<BattleHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const limit = 10;

  useEffect(() => {
    loadHistory(currentPage);
  }, [currentPage]);

  const loadHistory = async (page: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getBattleHistory(page, limit);
      setHistory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  const handleBattleClick = (battleId: string) => {
    router.push(`/battle/${battleId}`);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const renderWinner = (battle: BattleHistoryItem) => {
    const winner = battle.winner;

    if (!winner) {
      return (
        <span className="text-gray-400 dark:text-gray-500 text-sm">
          No feedback
        </span>
      );
    }
    if (winner === "tie") {
      return (
        <div className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
          <Users className="h-4 w-4" />
          <span className="text-sm font-medium">Both Good</span>
        </div>
      );
    }
    if (winner === "none") {
      return (
        <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
          <Minus className="h-4 w-4" />
          <span className="text-sm font-medium">Both Bad</span>
        </div>
      );
    }

    // Show model display name if available, otherwise show provider name
    const modelNames = battle.model_display_names;
    const displayName = (modelNames && modelNames[winner]) || winner;
    return (
      <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
        <Trophy className="h-4 w-4" />
        <span className="text-sm font-medium">{displayName}</span>
      </div>
    );
  };

  const getModelText = (battle: BattleHistoryItem) => {
    const modelNames = battle.model_display_names;
    if (!modelNames || Object.keys(modelNames).length === 0) {
      return "LlamaIndex vs Reducto";
    }

    const llamaModel = modelNames.llamaindex || "LlamaIndex";
    const reductoModel = modelNames.reducto || "Reducto";

    // Get pricing info based on model names
    const getLlamaPrice = (name: string) => {
      if (name === "Cost-effective") return "$0.003/page";
      if (name === "Agentic") return "$0.010/page";
      if (name === "Agentic Plus") return "$0.090/page";
      return "";
    };

    const getReductoPrice = (name: string) => {
      if (name === "Standard") return "$0.015/page";
      if (name === "Complex VLM") return "$0.030/page";
      return "";
    };

    const llamaPrice = getLlamaPrice(llamaModel);
    const reductoPrice = getReductoPrice(reductoModel);

    return `${llamaModel}${llamaPrice ? ` (${llamaPrice})` : ""} vs ${reductoModel}${reductoPrice ? ` (${reductoPrice})` : ""}`;
  };

  if (loading && !history) {
    return (
      <div className="mt-8 p-8 text-center text-gray-500 dark:text-gray-400">
        Loading battle history...
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-8 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <p className="text-red-600 dark:text-red-400">{error}</p>
      </div>
    );
  }

  if (!history || history.battles.length === 0) {
    return (
      <div className="mt-8 p-8 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-center gap-2 text-gray-500 dark:text-gray-400">
          <History className="h-5 w-5" />
          <span>No battle history yet</span>
        </div>
      </div>
    );
  }

  const totalPages = Math.ceil(history.total / limit);

  return (
    <div className="mt-8">
      <div className="flex items-center gap-2 mb-4">
        <History className="h-5 w-5 text-gray-700 dark:text-gray-300" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
          Battle History
        </h2>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          ({history.total} total)
        </span>
      </div>

      <div className="space-y-2">
        {history.battles.map((battle) => (
          <button
            key={battle.battle_id}
            onClick={() => handleBattleClick(battle.battle_id)}
            className="w-full p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-md transition-all text-left"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 dark:text-gray-100 truncate">
                  {battle.original_name}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Page {battle.page_number} • {formatDate(battle.created_at)}
                  </p>
                  <span className="text-xs text-gray-400 dark:text-gray-500">•</span>
                  <p className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                    {getModelText(battle)}
                  </p>
                </div>
              </div>
              <div className="flex-shrink-0">
                {renderWinner(battle)}
              </div>
            </div>
          </button>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-6">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
}
