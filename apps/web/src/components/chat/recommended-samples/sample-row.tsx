/**
 * Sample Row
 *
 * Individual row with checkbox, data cells, and expandable details accordion.
 */

"use client";

import { ChevronDown, Snowflake, FlaskConical } from "lucide-react";
import { RecommendedSample } from "./types";

interface SampleRowProps {
  sample: RecommendedSample;
  isSelected: boolean;
  isExpanded: boolean;
  onSelect: (checked: boolean) => void;
  onExpand: () => void;
}

export function SampleRow({
  sample,
  isSelected,
  isExpanded,
  onSelect,
  onExpand,
}: SampleRowProps) {
  return (
    <>
      {/* Main row */}
      <tr
        className={`
          border-b border-border transition-colors cursor-pointer
          ${isSelected ? "bg-primary/10" : "bg-secondary hover:bg-muted/70"}
        `}
        onClick={onExpand}
      >
        {/* Checkbox */}
        <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
          <Checkbox
            checked={isSelected}
            onChange={onSelect}
            aria-label={`Select sample ${sample.externalId}`}
          />
        </td>

        {/* ID */}
        <td className="px-4 py-3">
          <span className="text-sm font-medium text-foreground">
            {sample.externalId}
          </span>
        </td>

        {/* Type badge */}
        <td className="px-4 py-3">
          <TypeBadge type={sample.type} />
        </td>

        {/* RIN - color coded */}
        <td className="px-4 py-3">
          <RinValue value={sample.rin} />
        </td>

        {/* Age */}
        <td className="px-4 py-3">
          <span className="text-sm text-foreground">
            {sample.age != null ? `${sample.age}y` : "—"}
          </span>
        </td>

        {/* Price */}
        <td className="px-4 py-3">
          <span className="text-sm font-medium text-foreground">
            {sample.price != null ? `$${sample.price}` : "—"}
          </span>
        </td>

        {/* Expand chevron */}
        <td className="px-4 py-3">
          <ChevronDown
            className={`h-4 w-4 text-muted-foreground transition-transform ${
              isExpanded ? "rotate-180" : ""
            }`}
          />
        </td>
      </tr>

      {/* Expanded details */}
      {isExpanded && (
        <tr className="bg-muted/30">
          <td colSpan={7} className="px-4 py-4">
            <ExpandedDetails sample={sample} />
          </td>
        </tr>
      )}
    </>
  );
}

/**
 * Checkbox component
 */
function Checkbox({
  checked,
  onChange,
  "aria-label": ariaLabel,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  "aria-label"?: string;
}) {
  return (
    <button
      role="checkbox"
      aria-checked={checked}
      aria-label={ariaLabel}
      onClick={() => onChange(!checked)}
      className={`
        w-5 h-5 rounded border-2 flex items-center justify-center transition-colors
        ${
          checked
            ? "bg-primary border-primary"
            : "bg-transparent border-muted-foreground/50 hover:border-muted-foreground"
        }
      `}
    >
      {checked && (
        <svg
          className="w-3 h-3 text-primary-foreground"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={3}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      )}
    </button>
  );
}

/**
 * Type badge (Frozen/FFPE)
 */
function TypeBadge({ type }: { type: RecommendedSample["type"] }) {
  const config = {
    Frozen: {
      icon: Snowflake,
      bg: "bg-sky-900/40",
      border: "border-sky-700/50",
      text: "text-sky-200",
    },
    FFPE: {
      icon: FlaskConical,
      bg: "bg-amber-900/40",
      border: "border-amber-700/50",
      text: "text-amber-200",
    },
    Fresh: {
      icon: FlaskConical,
      bg: "bg-emerald-900/40",
      border: "border-emerald-700/50",
      text: "text-emerald-200",
    },
  };

  const { icon: Icon, bg, border, text } = config[type] || config.Fresh;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium border ${bg} ${border} ${text}`}
    >
      <Icon className="h-3 w-3" />
      {type}
    </span>
  );
}

/**
 * RIN value with color coding
 */
function RinValue({ value }: { value: number | null }) {
  if (value == null) {
    return <span className="text-sm text-muted-foreground">—</span>;
  }

  // Color based on quality
  const getColor = (rin: number) => {
    if (rin >= 8) return "text-teal-400";
    if (rin >= 7) return "text-foreground";
    if (rin >= 5) return "text-amber-400";
    return "text-red-400";
  };

  return (
    <span className={`text-sm font-medium ${getColor(value)}`}>
      {value.toFixed(1)}
    </span>
  );
}

/**
 * Expanded details section
 */
function ExpandedDetails({ sample }: { sample: RecommendedSample }) {
  const details = [
    { label: "Diagnosis", value: sample.diagnosis },
    { label: "Braak Stage", value: sample.braakStage },
    { label: "Sex", value: sample.sex },
    { label: "Source Bank", value: sample.sourceBank },
    { label: "Tissue Region", value: sample.details?.tissueRegion },
    { label: "Collection Date", value: sample.details?.collectionDate },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {details.map(
        (detail, index) =>
          detail.value && (
            <div key={index}>
              <dt className="text-xs text-muted-foreground uppercase tracking-wide">
                {detail.label}
              </dt>
              <dd className="text-sm text-foreground mt-0.5">{detail.value}</dd>
            </div>
          )
      )}

      {/* Pathology notes (full width) */}
      {sample.details?.pathologyNotes && (
        <div className="col-span-full">
          <dt className="text-xs text-muted-foreground uppercase tracking-wide">
            Pathology Notes
          </dt>
          <dd className="text-sm text-foreground mt-0.5">
            {sample.details.pathologyNotes}
          </dd>
        </div>
      )}

      {/* Donor history (full width) */}
      {sample.details?.donorHistory && (
        <div className="col-span-full">
          <dt className="text-xs text-muted-foreground uppercase tracking-wide">
            Donor History
          </dt>
          <dd className="text-sm text-foreground mt-0.5">
            {sample.details.donorHistory}
          </dd>
        </div>
      )}
    </div>
  );
}

