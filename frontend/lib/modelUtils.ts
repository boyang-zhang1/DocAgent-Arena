import { LlamaIndexConfig, ReductoConfig } from "@/types/api";

export interface ModelOption {
  value: string;
  label: string;
  description: string;
  credits: number;
}

export const LLAMAINDEX_MODELS: ModelOption[] = [
  {
    value: "parse_page_with_llm:default",
    label: "Cost-effective",
    description: "3 credits/page ($0.003/page)",
    credits: 3,
  },
  {
    value: "parse_page_with_agent:openai-gpt-4-1-mini",
    label: "Agentic",
    description: "10 credits/page ($0.010/page)",
    credits: 10,
  },
  {
    value: "parse_page_with_agent:anthropic-sonnet-4.0",
    label: "Agentic Plus",
    description: "90 credits/page ($0.090/page)",
    credits: 90,
  },
];

export const REDUCTO_MODELS: ModelOption[] = [
  {
    value: "standard",
    label: "Standard",
    description: "1 credit/page ($0.015/page)",
    credits: 1,
  },
  {
    value: "complex",
    label: "Complex VLM",
    description: "2 credits/page ($0.030/page)",
    credits: 2,
  },
];

export function getDefaultBattleConfigs() {
  return {
    llamaindex: {
      parse_mode: "parse_page_with_agent",
      model: "openai-gpt-4-1-mini",
    } as LlamaIndexConfig,
    reducto: {
      mode: "standard",
      summarize_figures: false,
    } as ReductoConfig,
  };
}

export function getLlamaIndexDisplayName(config: LlamaIndexConfig): string {
  const value = `${config.parse_mode}:${config.model}`;
  const model = LLAMAINDEX_MODELS.find((m) => m.value === value);
  return model?.label || "Agentic";
}

export function getReductoDisplayName(config: ReductoConfig): string {
  const model = REDUCTO_MODELS.find((m) => m.value === config.mode);
  return model?.label || "Standard";
}

export function llamaIndexConfigToValue(config: LlamaIndexConfig): string {
  return `${config.parse_mode}:${config.model}`;
}

export function valueToLlamaIndexConfig(value: string): LlamaIndexConfig {
  const [parse_mode, model] = value.split(":");
  return { parse_mode, model };
}

export function reductoConfigToValue(config: ReductoConfig): string {
  return config.mode;
}

export function valueToReductoConfig(value: string): ReductoConfig {
  return {
    mode: value,
    summarize_figures: value === "complex",
  };
}

export function getModelCredits(provider: string, config: LlamaIndexConfig | ReductoConfig): number {
  if (provider === "llamaindex") {
    const value = llamaIndexConfigToValue(config as LlamaIndexConfig);
    const model = LLAMAINDEX_MODELS.find((m) => m.value === value);
    return model?.credits || 10;
  } else if (provider === "reducto") {
    const value = reductoConfigToValue(config as ReductoConfig);
    const model = REDUCTO_MODELS.find((m) => m.value === value);
    return model?.credits || 1;
  }
  return 0;
}
