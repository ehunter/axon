/**
 * Sample Request Form
 *
 * Collects researcher and institutional information required by brain banks
 * when requesting human brain tissue samples.
 */

"use client";

import { useEffect, useRef, useState } from "react";
import { Send, X, User, Building2, MapPin, FileCheck, Beaker } from "lucide-react";
import { RecommendedSample, SampleRequestConfig, OrderConfig } from "./types";

interface ConfigFormProps {
  selectedSamples: RecommendedSample[];
  config: OrderConfig; // Legacy prop - kept for compatibility
  onConfigChange: (config: OrderConfig) => void; // Legacy prop
  onSubmit: () => void;
  onCancel: () => void;
}

const INITIAL_REQUEST_CONFIG: SampleRequestConfig = {
  piName: "",
  piEmail: "",
  piPhone: "",
  institution: "",
  department: "",
  shippingAddress: "",
  shippingCity: "",
  shippingState: "",
  shippingZip: "",
  shippingCountry: "United States",
  irbApproval: "",
  irbExpirationDate: "",
  grantNumber: "",
  fundingSource: "",
  projectTitle: "",
  intendedUse: "",
};

export function ConfigForm({
  selectedSamples,
  onSubmit,
  onCancel,
}: ConfigFormProps) {
  const formRef = useRef<HTMLDivElement>(null);
  const [requestConfig, setRequestConfig] = useState<SampleRequestConfig>(INITIAL_REQUEST_CONFIG);
  const [errors, setErrors] = useState<Partial<Record<keyof SampleRequestConfig, string>>>({});

  // Auto-scroll into view when form appears
  useEffect(() => {
    if (formRef.current) {
      formRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, []);

  const updateField = (field: keyof SampleRequestConfig, value: string) => {
    setRequestConfig((prev) => ({ ...prev, [field]: value }));
    // Clear error when field is updated
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof SampleRequestConfig, string>> = {};
    
    // Required fields
    if (!requestConfig.piName.trim()) newErrors.piName = "Required";
    if (!requestConfig.piEmail.trim()) newErrors.piEmail = "Required";
    if (!requestConfig.institution.trim()) newErrors.institution = "Required";
    if (!requestConfig.shippingAddress.trim()) newErrors.shippingAddress = "Required";
    if (!requestConfig.shippingCity.trim()) newErrors.shippingCity = "Required";
    if (!requestConfig.shippingState.trim()) newErrors.shippingState = "Required";
    if (!requestConfig.shippingZip.trim()) newErrors.shippingZip = "Required";
    if (!requestConfig.irbApproval.trim()) newErrors.irbApproval = "Required";
    if (!requestConfig.projectTitle.trim()) newErrors.projectTitle = "Required";
    if (!requestConfig.intendedUse.trim()) newErrors.intendedUse = "Required";
    
    // Email validation
    if (requestConfig.piEmail && !requestConfig.piEmail.includes("@")) {
      newErrors.piEmail = "Invalid email";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      // TODO: Include requestConfig in the submission
      onSubmit();
    }
  };

  const caseCount = selectedSamples.filter((s) => s.sampleGroup === "case").length;
  const controlCount = selectedSamples.filter((s) => s.sampleGroup === "control").length;

  return (
    <div
      ref={formRef}
      className="border-t border-muted-foreground/30 bg-muted/30 px-5 py-5 animate-in slide-in-from-top-2 duration-300"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h4 className="text-base font-semibold text-foreground">
            Sample Request Form
          </h4>
          <p className="text-sm text-muted-foreground mt-0.5">
            {selectedSamples.length} sample{selectedSamples.length !== 1 ? "s" : ""} selected
            {caseCount > 0 && controlCount > 0 && (
              <span className="ml-1">
                ({caseCount} case{caseCount !== 1 ? "s" : ""}, {controlCount} control{controlCount !== 1 ? "s" : ""})
              </span>
            )}
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

      <div className="space-y-6">
        {/* Principal Investigator */}
        <FormSection
          icon={<User className="h-4 w-4" />}
          title="Principal Investigator"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <FormField
              label="Full Name"
              required
              value={requestConfig.piName}
              onChange={(v) => updateField("piName", v)}
              error={errors.piName}
              placeholder="Dr. Jane Smith"
            />
            <FormField
              label="Email"
              required
              type="email"
              value={requestConfig.piEmail}
              onChange={(v) => updateField("piEmail", v)}
              error={errors.piEmail}
              placeholder="jsmith@university.edu"
            />
            <FormField
              label="Phone"
              value={requestConfig.piPhone}
              onChange={(v) => updateField("piPhone", v)}
              placeholder="+1 (555) 123-4567"
            />
          </div>
        </FormSection>

        {/* Institution */}
        <FormSection
          icon={<Building2 className="h-4 w-4" />}
          title="Institution"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <FormField
              label="Institution Name"
              required
              value={requestConfig.institution}
              onChange={(v) => updateField("institution", v)}
              error={errors.institution}
              placeholder="University of California"
            />
            <FormField
              label="Department"
              value={requestConfig.department}
              onChange={(v) => updateField("department", v)}
              placeholder="Department of Neuroscience"
            />
          </div>
        </FormSection>

        {/* Shipping Address */}
        <FormSection
          icon={<MapPin className="h-4 w-4" />}
          title="Shipping Address"
          subtitle="Must be an institutional address"
        >
          <div className="space-y-3">
            <FormField
              label="Street Address"
              required
              value={requestConfig.shippingAddress}
              onChange={(v) => updateField("shippingAddress", v)}
              error={errors.shippingAddress}
              placeholder="123 Research Drive, Building A, Room 456"
            />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <FormField
                label="City"
                required
                value={requestConfig.shippingCity}
                onChange={(v) => updateField("shippingCity", v)}
                error={errors.shippingCity}
                placeholder="San Francisco"
              />
              <FormField
                label="State"
                required
                value={requestConfig.shippingState}
                onChange={(v) => updateField("shippingState", v)}
                error={errors.shippingState}
                placeholder="CA"
              />
              <FormField
                label="ZIP Code"
                required
                value={requestConfig.shippingZip}
                onChange={(v) => updateField("shippingZip", v)}
                error={errors.shippingZip}
                placeholder="94102"
              />
              <FormField
                label="Country"
                value={requestConfig.shippingCountry}
                onChange={(v) => updateField("shippingCountry", v)}
                placeholder="United States"
              />
            </div>
          </div>
        </FormSection>

        {/* IRB & Compliance */}
        <FormSection
          icon={<FileCheck className="h-4 w-4" />}
          title="IRB Approval"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <FormField
              label="IRB Protocol Number"
              required
              value={requestConfig.irbApproval}
              onChange={(v) => updateField("irbApproval", v)}
              error={errors.irbApproval}
              placeholder="IRB-2024-0123 or 'Exempt'"
            />
            <FormField
              label="Expiration Date"
              type="date"
              value={requestConfig.irbExpirationDate}
              onChange={(v) => updateField("irbExpirationDate", v)}
            />
          </div>
        </FormSection>

        {/* Project Details */}
        <FormSection
          icon={<Beaker className="h-4 w-4" />}
          title="Project Details"
        >
          <div className="space-y-3">
            <FormField
              label="Project Title"
              required
              value={requestConfig.projectTitle}
              onChange={(v) => updateField("projectTitle", v)}
              error={errors.projectTitle}
              placeholder="Transcriptomic Analysis of Alzheimer's Disease Progression"
            />
            <FormField
              label="Intended Use"
              required
              value={requestConfig.intendedUse}
              onChange={(v) => updateField("intendedUse", v)}
              error={errors.intendedUse}
              placeholder="RNA-seq, proteomics, immunohistochemistry, etc."
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <FormField
                label="Grant/Funding Number"
                value={requestConfig.grantNumber}
                onChange={(v) => updateField("grantNumber", v)}
                placeholder="R01-AG123456 (optional)"
              />
              <FormField
                label="Funding Source"
                value={requestConfig.fundingSource}
                onChange={(v) => updateField("fundingSource", v)}
                placeholder="NIH, Alzheimer's Association, etc. (optional)"
              />
            </div>
          </div>
        </FormSection>
      </div>

      {/* Footer with actions */}
      <div className="flex items-center justify-between pt-5 mt-5 border-t border-muted-foreground/30">
        <p className="text-xs text-muted-foreground max-w-md">
          By submitting, you confirm that all information is accurate and tissue will be used 
          in accordance with ethical guidelines for human tissue research.
        </p>

        <div className="flex items-center gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm font-medium border border-border bg-secondary text-foreground hover:bg-muted transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Send className="h-4 w-4" />
            Submit Request
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Form section with icon and title
 */
function FormSection({
  icon,
  title,
  subtitle,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-muted-foreground">{icon}</span>
        <h5 className="text-sm font-semibold text-foreground">{title}</h5>
        {subtitle && (
          <span className="text-xs text-muted-foreground">({subtitle})</span>
        )}
      </div>
      {children}
    </div>
  );
}

/**
 * Individual form field
 */
function FormField({
  label,
  required,
  type = "text",
  value,
  onChange,
  error,
  placeholder,
}: {
  label: string;
  required?: boolean;
  type?: "text" | "email" | "date";
  value: string;
  onChange: (value: string) => void;
  error?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-muted-foreground mb-1">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`
          w-full px-3 py-1.5 rounded-md bg-input border text-foreground text-sm
          placeholder:text-muted-foreground/50
          focus:outline-none focus:ring-2 focus:ring-primary/50
          ${error ? "border-red-400" : "border-border"}
        `}
      />
      {error && <p className="text-xs text-red-400 mt-0.5">{error}</p>}
    </div>
  );
}
