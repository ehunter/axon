/**
 * Config Form
 *
 * Inline order configuration form with progressive disclosure.
 */

"use client";

import { useMemo, useEffect, useRef } from "react";
import { Package, Truck, Send, X } from "lucide-react";
import { RecommendedSample, OrderConfig, PriceEstimate } from "./types";

interface ConfigFormProps {
  selectedSamples: RecommendedSample[];
  config: OrderConfig;
  onConfigChange: (config: OrderConfig) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

export function ConfigForm({
  selectedSamples,
  config,
  onConfigChange,
  onSubmit,
  onCancel,
}: ConfigFormProps) {
  const formRef = useRef<HTMLDivElement>(null);

  // Auto-scroll into view when form appears
  useEffect(() => {
    if (formRef.current) {
      formRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, []);

  // Calculate price estimate
  const priceEstimate = useMemo<PriceEstimate>(() => {
    const basePrice = selectedSamples.reduce((sum, s) => sum + (s.price || 0), 0);
    
    // Format multiplier
    const formatMultiplier = {
      slide: 1,
      block: 1.5,
      shavings: 0.8,
    };

    const subtotal = basePrice * config.quantity * formatMultiplier[config.format];
    const shippingCost = config.shippingPriority === "overnight" ? 75 : 15;
    
    return {
      subtotal: Math.round(subtotal),
      shippingCost,
      total: Math.round(subtotal + shippingCost),
    };
  }, [selectedSamples, config]);

  return (
    <div
      ref={formRef}
      className="border-t border-border bg-muted/30 px-5 py-5 animate-in slide-in-from-top-2 duration-300"
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h4 className="text-base font-semibold text-foreground">
            Configure Your Order
          </h4>
          <p className="text-sm text-muted-foreground mt-0.5">
            {selectedSamples.length} sample{selectedSamples.length !== 1 ? "s" : ""} selected
          </p>
        </div>
        <button
          onClick={onCancel}
          className="p-1 rounded-md hover:bg-muted transition-colors"
          aria-label="Cancel"
        >
          <X className="h-5 w-5 text-muted-foreground" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Format dropdown */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">
            <Package className="h-4 w-4 inline-block mr-1.5 text-muted-foreground" />
            Format
          </label>
          <select
            value={config.format}
            onChange={(e) =>
              onConfigChange({ ...config, format: e.target.value as OrderConfig["format"] })
            }
            className="w-full px-3 py-2 rounded-lg bg-input border border-border text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          >
            <option value="slide">Slide</option>
            <option value="block">Block</option>
            <option value="shavings">Shavings</option>
          </select>
        </div>

        {/* Quantity input */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">
            Quantity (per sample)
          </label>
          <input
            type="number"
            min={1}
            max={10}
            value={config.quantity}
            onChange={(e) =>
              onConfigChange({ ...config, quantity: Math.max(1, parseInt(e.target.value) || 1) })
            }
            className="w-full px-3 py-2 rounded-lg bg-input border border-border text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        {/* Shipping priority */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">
            <Truck className="h-4 w-4 inline-block mr-1.5 text-muted-foreground" />
            Shipping
          </label>
          <div className="flex gap-2">
            <ShippingOption
              label="Standard"
              value="standard"
              selected={config.shippingPriority === "standard"}
              onClick={() => onConfigChange({ ...config, shippingPriority: "standard" })}
            />
            <ShippingOption
              label="Overnight"
              value="overnight"
              selected={config.shippingPriority === "overnight"}
              onClick={() => onConfigChange({ ...config, shippingPriority: "overnight" })}
            />
          </div>
        </div>
      </div>

      {/* Price summary and submit */}
      <div className="flex items-center justify-between pt-4 border-t border-border">
        <div className="space-y-0.5">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>Subtotal: ${priceEstimate.subtotal}</span>
            <span>Shipping: ${priceEstimate.shippingCost}</span>
          </div>
          <div className="text-lg font-semibold text-foreground">
            Estimated Total: ${priceEstimate.total}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm font-medium border border-border bg-secondary text-foreground hover:bg-muted transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onSubmit}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Send className="h-4 w-4" />
            Send Request
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Shipping option toggle button
 */
function ShippingOption({
  label,
  value,
  selected,
  onClick,
}: {
  label: string;
  value: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        flex-1 px-3 py-2 rounded-lg text-sm font-medium border transition-colors
        ${
          selected
            ? "bg-primary/20 border-primary text-primary"
            : "bg-input border-border text-foreground hover:bg-muted"
        }
      `}
    >
      {label}
    </button>
  );
}

