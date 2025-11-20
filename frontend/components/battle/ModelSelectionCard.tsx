"use client";

import { useState, useEffect } from "react";
import { LlamaIndexConfig, ReductoConfig, LandingAIConfig, UnstructuredIOConfig } from "@/types/api";
import {
  ProviderPricingMap,
  llamaIndexConfigToValue,
  reductoConfigToValue,
  landingaiConfigToValue,
  unstructuredioConfigToValue,
  getModelOptionForConfig,
  formatOptionDescription,
  getFallbackLabel,
  PresetMode,
  detectPresetFromConfigs,
  getConfigsForPreset,
} from "@/lib/modelUtils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { ProviderLabel } from "@/components/providers/ProviderLabel";

interface ModelSelectionCardProps {
  selectedConfigs: {
    llamaindex: LlamaIndexConfig;
    reducto: ReductoConfig;
    landingai: LandingAIConfig;
    unstructuredio: UnstructuredIOConfig;
  };
  onConfigChange?: (configs: {
    llamaindex: LlamaIndexConfig;
    reducto: ReductoConfig;
    landingai: LandingAIConfig;
    unstructuredio: UnstructuredIOConfig;
  }) => void;
  readOnly?: boolean;
  pricing?: ProviderPricingMap | null;
  pricingLoading?: boolean;
  pricingError?: string | null;
  debugMode?: boolean;
  enabledProviders?: string[];
  onProviderToggle?: (provider: string, enabled: boolean) => void;
}

export function ModelSelectionCard({
  selectedConfigs,
  onConfigChange,
  readOnly = false,
  pricing,
  pricingLoading = false,
  pricingError = null,
  debugMode = false,
  enabledProviders = [],
  onProviderToggle,
}: ModelSelectionCardProps) {
  // Track the current preset mode (standard, advance, or custom)
  const [presetMode, setPresetMode] = useState<PresetMode>("standard");

  // Detect which preset (if any) matches the current configs
  useEffect(() => {
    const detectedPreset = detectPresetFromConfigs(selectedConfigs);
    setPresetMode(detectedPreset);
  }, [selectedConfigs]);

  // Handle toggle change between standard and advance
  const handlePresetToggle = (checked: boolean) => {
    if (readOnly || !onConfigChange || !pricing) return;

    const newPreset = checked ? "advance" : "standard";
    const newConfigs = getConfigsForPreset(newPreset, pricing);

    if (newConfigs) {
      onConfigChange(newConfigs);
    }
  };

  const handleLlamaIndexChange = (value: string) => {
    if (readOnly || !onConfigChange) return;
    const option = pricing?.llamaindex?.models.find((model) => model.value === value);
    if (!option) return;
    onConfigChange({
      ...selectedConfigs,
      llamaindex: option.config as LlamaIndexConfig,
    });
  };

  const handleReductoChange = (value: string) => {
    if (readOnly || !onConfigChange) return;
    const option = pricing?.reducto?.models.find((model) => model.value === value);
    if (!option) return;
    onConfigChange({
      ...selectedConfigs,
      reducto: option.config as ReductoConfig,
    });
  };

  const handleLandingAIChange = (value: string) => {
    if (readOnly || !onConfigChange) return;
    const option = pricing?.landingai?.models.find((model) => model.value === value);
    if (!option) return;
    onConfigChange({
      ...selectedConfigs,
      landingai: option.config as LandingAIConfig,
    });
  };

  const handleUnstructuredIOChange = (value: string) => {
    if (readOnly || !onConfigChange) return;
    const option = pricing?.unstructuredio?.models.find((model) => model.value === value);
    if (!option) return;
    onConfigChange({
      ...selectedConfigs,
      unstructuredio: option.config as UnstructuredIOConfig,
    });
  };

  if (!pricing) {
    return (
      <div className="rounded-xl border border-purple-200 bg-purple-50/70 dark:border-purple-900/50 dark:bg-purple-950/30 px-4 pt-2 pb-4">
        <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-100 mb-3">
          {readOnly ? "Models used in this battle" : "Model Selection"}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {pricingLoading
            ? "Loading provider pricing..."
            : pricingError || "Pricing data unavailable."}
        </p>
      </div>
    );
  }

  const llamaOptions = pricing.llamaindex?.models ?? [];
  const reductoOptions = pricing.reducto?.models ?? [];
  const landingaiOptions = pricing.landingai?.models ?? [];
  const unstructuredioOptions = pricing.unstructuredio?.models ?? [];

  const llamaSelection = getModelOptionForConfig(
    "llamaindex",
    selectedConfigs.llamaindex,
    pricing
  );
  const reductoSelection = getModelOptionForConfig(
    "reducto",
    selectedConfigs.reducto,
    pricing
  );
  const landingaiSelection = getModelOptionForConfig(
    "landingai",
    selectedConfigs.landingai,
    pricing
  );
  const unstructuredioSelection = getModelOptionForConfig(
    "unstructuredio",
    selectedConfigs.unstructuredio,
    pricing
  );

  return (
    <div className="rounded-xl border border-purple-200 bg-purple-50/70 dark:border-purple-900/50 dark:bg-purple-950/30 px-4 pt-2 pb-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-100">
            {readOnly ? "Models used in this battle" : "Model Selection"}
          </h3>
          {debugMode && !readOnly && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 font-medium">
              Debug Mode
            </span>
          )}
        </div>

        {/* Preset toggle - only show in edit mode */}
        {!readOnly && (
          <div className="flex items-center gap-3">
            {presetMode === "custom" && (
              <span className="text-sm text-purple-600 dark:text-purple-400 font-medium">
                (Custom)
              </span>
            )}
            <div className="inline-flex rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800 p-1">
              <button
                onClick={() => handlePresetToggle(false)}
                disabled={!pricing}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                  presetMode === "standard"
                    ? "bg-white dark:bg-gray-700 text-purple-600 dark:text-purple-400 shadow-sm"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                }`}
              >
                Standard
              </button>
              <button
                onClick={() => handlePresetToggle(true)}
                disabled={!pricing}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                  presetMode === "advance"
                    ? "bg-white dark:bg-gray-700 text-purple-600 dark:text-purple-400 shadow-sm"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                }`}
              >
                Advance
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-4 gap-6">
        {/* LlamaIndex Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            {debugMode && !readOnly && (
              <Checkbox
                checked={enabledProviders.includes("llamaindex")}
                onCheckedChange={(checked) => onProviderToggle?.("llamaindex", !!checked)}
                disabled={enabledProviders.length <= 2 && enabledProviders.includes("llamaindex")}
              />
            )}
            <ProviderLabel provider="llamaindex" size={20} className="gap-2" nameClassName="text-sm font-medium" />
          </div>
          {readOnly ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-950 rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2">
              {llamaSelection?.label || getFallbackLabel("llamaindex")}
            </div>
          ) : (
            <Select
              value={llamaIndexConfigToValue(selectedConfigs.llamaindex)}
              onValueChange={handleLlamaIndexChange}
              disabled={!llamaOptions.length || (debugMode && !enabledProviders.includes("llamaindex"))}
            >
              <SelectTrigger id="llamaindex-model" className="bg-white dark:bg-gray-950">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {llamaOptions.map((model) => (
                  <SelectItem key={model.value} value={model.value}>
                    {formatOptionDescription(model)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Reducto Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            {debugMode && !readOnly && (
              <Checkbox
                checked={enabledProviders.includes("reducto")}
                onCheckedChange={(checked) => onProviderToggle?.("reducto", !!checked)}
                disabled={enabledProviders.length <= 2 && enabledProviders.includes("reducto")}
              />
            )}
            <ProviderLabel provider="reducto" size={20} className="gap-2" nameClassName="text-sm font-medium" />
          </div>
          {readOnly ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-950 rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2">
              {reductoSelection?.label || getFallbackLabel("reducto")}
            </div>
          ) : (
            <Select
              value={reductoConfigToValue(selectedConfigs.reducto)}
              onValueChange={handleReductoChange}
              disabled={!reductoOptions.length || (debugMode && !enabledProviders.includes("reducto"))}
            >
              <SelectTrigger id="reducto-mode" className="bg-white dark:bg-gray-950">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {reductoOptions.map((model) => (
                  <SelectItem key={model.value} value={model.value}>
                    {formatOptionDescription(model)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* LandingAI Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            {debugMode && !readOnly && (
              <Checkbox
                checked={enabledProviders.includes("landingai")}
                onCheckedChange={(checked) => onProviderToggle?.("landingai", !!checked)}
                disabled={enabledProviders.length <= 2 && enabledProviders.includes("landingai")}
              />
            )}
            <ProviderLabel provider="landingai" size={20} className="gap-2" nameClassName="text-sm font-medium" />
          </div>
          {readOnly ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-950 rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2">
              {landingaiSelection?.label || getFallbackLabel("landingai")}
            </div>
          ) : (
            <Select
              value={landingaiConfigToValue(selectedConfigs.landingai)}
              onValueChange={handleLandingAIChange}
              disabled={!landingaiOptions.length || (debugMode && !enabledProviders.includes("landingai"))}
            >
              <SelectTrigger id="landingai-model" className="bg-white dark:bg-gray-950">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {landingaiOptions.map((model) => (
                  <SelectItem key={model.value} value={model.value}>
                    {formatOptionDescription(model)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Unstructured.io Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            {debugMode && !readOnly && (
              <Checkbox
                checked={enabledProviders.includes("unstructuredio")}
                onCheckedChange={(checked) => onProviderToggle?.("unstructuredio", !!checked)}
                disabled={enabledProviders.length <= 2 && enabledProviders.includes("unstructuredio")}
              />
            )}
            <ProviderLabel provider="unstructuredio" size={20} className="gap-2" nameClassName="text-sm font-medium" />
          </div>
          {readOnly ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-950 rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2">
              {unstructuredioSelection?.label || getFallbackLabel("unstructuredio")}
            </div>
          ) : (
            <Select
              value={unstructuredioConfigToValue(selectedConfigs.unstructuredio)}
              onValueChange={handleUnstructuredIOChange}
              disabled={!unstructuredioOptions.length || (debugMode && !enabledProviders.includes("unstructuredio"))}
            >
              <SelectTrigger id="unstructuredio-mode" className="bg-white dark:bg-gray-950">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {unstructuredioOptions.map((model) => (
                  <SelectItem key={model.value} value={model.value}>
                    {formatOptionDescription(model)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
      </div>
    </div>
  );
}
