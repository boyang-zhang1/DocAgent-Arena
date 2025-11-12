"use client";

import { useEffect, useMemo, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { ProviderPricingInfo } from "@/types/api";

let cachedPricing: ProviderPricingInfo[] | null = null;
let pendingRequest: Promise<ProviderPricingInfo[]> | null = null;

export function useProviderPricing() {
  const [pricing, setPricing] = useState<ProviderPricingInfo[] | null>(cachedPricing);
  const [loading, setLoading] = useState(!cachedPricing);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cachedPricing) {
      setPricing(cachedPricing);
      setLoading(false);
      return;
    }

    let isMounted = true;

    if (!pendingRequest) {
      pendingRequest = apiClient.getProviderPricing();
    }

    pendingRequest
      .then((data) => {
        cachedPricing = data;
        if (isMounted) {
          setPricing(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load pricing");
        }
      })
      .finally(() => {
        if (pendingRequest) {
          pendingRequest = null;
        }
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const pricingMap = useMemo(() => {
    if (!pricing) return null;
    return pricing.reduce<Record<string, ProviderPricingInfo>>((acc, info) => {
      acc[info.provider] = info;
      return acc;
    }, {});
  }, [pricing]);

  return {
    pricing,
    pricingMap,
    loading,
    error,
  };
}
