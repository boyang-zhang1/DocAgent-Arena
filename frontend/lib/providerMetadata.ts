export interface ProviderInfo {
  displayName: string;
  logoSrc: string;
  alt: string;
}

export const PROVIDER_METADATA: Record<string, ProviderInfo> = {
  llamaindex: {
    displayName: "LlamaIndex",
    logoSrc: "/llamaindex.png",
    alt: "LlamaIndex logo",
  },
  landingai: {
    displayName: "LandingAI",
    logoSrc: "/landingai.png",
    alt: "LandingAI logo",
  },
  reducto: {
    displayName: "Reducto",
    logoSrc: "/reducto.svg",
    alt: "Reducto logo",
  },
  unstructuredio: {
    displayName: "Unstructured.io",
    logoSrc: "/unstructured.png",
    alt: "Unstructured.io logo",
  },
  extendai: {
    displayName: "ExtendAI",
    logoSrc: "/extendai.png",
    alt: "ExtendAI logo",
  },
};

export function getProviderInfo(provider: string): ProviderInfo | undefined {
  return PROVIDER_METADATA[provider];
}

export function getProviderDisplayName(provider: string): string {
  return getProviderInfo(provider)?.displayName ?? provider;
}
