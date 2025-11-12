"use client";

import { LlamaIndexConfig, ReductoConfig } from "@/types/api";
import {
  LLAMAINDEX_MODELS,
  REDUCTO_MODELS,
  llamaIndexConfigToValue,
  reductoConfigToValue,
  valueToLlamaIndexConfig,
  valueToReductoConfig,
  getLlamaIndexDisplayName,
  getReductoDisplayName,
} from "@/lib/modelUtils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { ProviderLabel } from "@/components/providers/ProviderLabel";

interface ModelSelectionCardProps {
  selectedConfigs: {
    llamaindex: LlamaIndexConfig;
    reducto: ReductoConfig;
  };
  onConfigChange?: (configs: {
    llamaindex: LlamaIndexConfig;
    reducto: ReductoConfig;
  }) => void;
  readOnly?: boolean;
}

export function ModelSelectionCard({
  selectedConfigs,
  onConfigChange,
  readOnly = false,
}: ModelSelectionCardProps) {
  const handleLlamaIndexChange = (value: string) => {
    if (readOnly || !onConfigChange) return;
    const newConfig = valueToLlamaIndexConfig(value);
    onConfigChange({
      ...selectedConfigs,
      llamaindex: newConfig,
    });
  };

  const handleReductoChange = (value: string) => {
    if (readOnly || !onConfigChange) return;
    const newConfig = valueToReductoConfig(value);
    onConfigChange({
      ...selectedConfigs,
      reducto: newConfig,
    });
  };

  return (
    <div className="rounded-xl border border-purple-200 bg-purple-50/70 dark:border-purple-900/50 dark:bg-purple-950/30 p-4">
      <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-100 mb-3">
        {readOnly ? "Models used in this battle" : "Model Selection"}
      </h3>

      <div className="grid grid-cols-2 gap-6">
        {/* LlamaIndex Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <ProviderLabel provider="llamaindex" size={20} className="gap-2" nameClassName="text-sm font-medium" />
          </div>
          {readOnly ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-950 rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2">
              {getLlamaIndexDisplayName(selectedConfigs.llamaindex)}
            </div>
          ) : (
            <div>
              <Label htmlFor="llamaindex-model" className="text-xs text-gray-600 dark:text-gray-400 mb-2 block">
                Model
              </Label>
              <Select
                value={llamaIndexConfigToValue(selectedConfigs.llamaindex)}
                onValueChange={handleLlamaIndexChange}
              >
                <SelectTrigger id="llamaindex-model" className="bg-white dark:bg-gray-950">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LLAMAINDEX_MODELS.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label} - {model.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* Reducto Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <ProviderLabel provider="reducto" size={20} className="gap-2" nameClassName="text-sm font-medium" />
          </div>
          {readOnly ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-950 rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2">
              {getReductoDisplayName(selectedConfigs.reducto)}
            </div>
          ) : (
            <div>
              <Label htmlFor="reducto-mode" className="text-xs text-gray-600 dark:text-gray-400 mb-2 block">
                Mode
              </Label>
              <Select
                value={reductoConfigToValue(selectedConfigs.reducto)}
                onValueChange={handleReductoChange}
              >
                <SelectTrigger id="reducto-mode" className="bg-white dark:bg-gray-950">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {REDUCTO_MODELS.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label} - {model.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
