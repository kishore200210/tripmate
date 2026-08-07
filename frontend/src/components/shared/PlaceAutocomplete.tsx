"use client";

/**
 * src/components/shared/PlaceAutocomplete.tsx
 *
 * A fully accessible, keyboard-navigable place search autocomplete component.
 * Calls the backend Nominatim proxy via usePlaceSearch with a debounced query.
 *
 * Accessibility:
 *   - role="combobox" on the input wrapper
 *   - aria-expanded, aria-autocomplete, aria-activedescendant
 *   - role="listbox" / role="option" on the dropdown
 *   - Keyboard: ArrowUp/Down to navigate, Enter to select, Escape to dismiss
 *
 * Usage:
 *   <PlaceAutocomplete value={selectedPlace} onChange={setSelectedPlace} />
 */

import { useState, useEffect, useRef, useId, KeyboardEvent } from "react";
import { MapPin, Loader2, X, Search } from "lucide-react";
import { usePlaceSearch } from "@/hooks/useDataAPI";
import type { PlaceResult } from "@/types";
import { cn } from "@/lib/utils";

// ── Country Code → Flag Emoji ──────────────────────────────────────────────────
function countryFlag(code: string | null | undefined): string {
  if (!code || code.length !== 2) return "🌍";
  // Convert ISO 3166-1 alpha-2 to regional indicator symbols
  return String.fromCodePoint(
    ...code.toUpperCase().split("").map((c) => 0x1f1e6 + c.charCodeAt(0) - 65)
  );
}

// ── Sub-label builder ──────────────────────────────────────────────────────────
function buildSubLabel(place: PlaceResult): string {
  const parts: string[] = [];
  if (place.state && place.state !== place.name) parts.push(place.state);
  if (place.country && place.country !== place.name) parts.push(place.country);
  if (place.place_type && place.place_type !== "City" && place.place_type !== "Country") {
    // Append type in parens only for non-obvious types
  }
  return parts.join(", ");
}

// ── Props ──────────────────────────────────────────────────────────────────────
interface PlaceAutocompleteProps {
  value: PlaceResult | null;
  onChange: (place: PlaceResult | null) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
  required?: boolean;
  "aria-label"?: string;
}

// ── Component ──────────────────────────────────────────────────────────────────
export function PlaceAutocomplete({
  value,
  onChange,
  placeholder = "Search any city, country or region…",
  disabled = false,
  className,
  id,
  required,
  "aria-label": ariaLabel,
}: PlaceAutocompleteProps) {
  const uid = useId();
  const inputId = id || `place-autocomplete-${uid}`;
  const listboxId = `${inputId}-listbox`;

  // Input text (what the user is typing)
  const [inputValue, setInputValue] = useState<string>(
    value ? value.name : ""
  );
  // Debounced query actually sent to the hook
  const [query, setQuery] = useState<string>("");
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Sync external value changes (e.g. form reset)
  useEffect(() => {
    setInputValue(value ? value.name : "");
    if (!value) setQuery("");
  }, [value]);

  // Debounce: update query 350ms after typing stops
  useEffect(() => {
    if (value) return; // Don't re-search if a place is already selected
    const timer = setTimeout(() => {
      setQuery(inputValue.trim());
    }, 350);
    return () => clearTimeout(timer);
  }, [inputValue, value]);

  const { data: results = [], isFetching } = usePlaceSearch(query);

  // Open dropdown when results arrive
  useEffect(() => {
    if (results.length > 0 && query.length >= 2) {
      setIsOpen(true);
      setActiveIndex(-1);
    }
  }, [results, query]);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Scroll active option into view
  useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const item = listRef.current.children[activeIndex] as HTMLElement | undefined;
      item?.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  const handleSelect = (place: PlaceResult) => {
    onChange(place);
    setInputValue(place.name);
    setQuery("");
    setIsOpen(false);
    setActiveIndex(-1);
  };

  const handleClear = () => {
    onChange(null);
    setInputValue("");
    setQuery("");
    setIsOpen(false);
    setActiveIndex(-1);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) {
      if (e.key === "ArrowDown" && results.length > 0) {
        setIsOpen(true);
        setActiveIndex(0);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, results.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        if (activeIndex >= 0 && results[activeIndex]) {
          handleSelect(results[activeIndex]);
        }
        break;
      case "Escape":
        e.preventDefault();
        setIsOpen(false);
        setActiveIndex(-1);
        break;
      case "Tab":
        setIsOpen(false);
        break;
    }
  };

  const isSelected = value !== null;
  const showSpinner = isFetching && query.length >= 2;
  const showNoResults =
    isOpen && !isFetching && query.length >= 2 && results.length === 0;

  return (
    <div ref={containerRef} className={cn("relative w-full", className)}>
      {/* Input wrapper with combobox role */}
      <div
        role="combobox"
        aria-expanded={isOpen}
        aria-controls={listboxId}
        aria-haspopup="listbox"
        aria-owns={listboxId}
        className="relative"
      >
        {/* Leading icon */}
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          {showSpinner ? (
            <Loader2 className="h-4 w-4 animate-spin text-neutral-400" />
          ) : (
            <Search className="h-4 w-4 text-neutral-400" />
          )}
        </div>

        <input
          ref={inputRef}
          id={inputId}
          type="text"
          role="searchbox"
          autoComplete="off"
          aria-label={ariaLabel || "Search destination"}
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-activedescendant={
            activeIndex >= 0 ? `${listboxId}-option-${activeIndex}` : undefined
          }
          value={inputValue}
          disabled={disabled}
          required={required}
          placeholder={placeholder}
          onChange={(e) => {
            setInputValue(e.target.value);
            if (value && e.target.value !== value.name) {
              // User is modifying the selected value — reset selection
              onChange(null);
            }
            if (e.target.value.trim().length >= 2) {
              setIsOpen(true);
            } else {
              setIsOpen(false);
            }
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (results.length > 0 && query.length >= 2) setIsOpen(true);
          }}
          className={cn(
            "h-9 w-full rounded-md border border-neutral-200 bg-white px-3 py-1 pl-9 pr-9 text-sm text-neutral-900",
            "placeholder:text-neutral-400 shadow-sm",
            "transition-colors outline-none",
            "focus-visible:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/20",
            "disabled:pointer-events-none disabled:opacity-50",
            isSelected && "border-blue-300 bg-blue-50/30"
          )}
        />

        {/* Clear button — only shown when a value is selected or text exists */}
        {(isSelected || inputValue) && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-neutral-400 hover:text-neutral-700 transition-colors"
            aria-label="Clear destination"
            tabIndex={-1}
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Selected place pill */}
      {isSelected && (
        <div className="mt-1.5 flex items-center gap-1.5 text-xs text-blue-700">
          <MapPin className="h-3 w-3 shrink-0" />
          <span className="truncate font-medium">
            {countryFlag(value!.country_code)} {value!.name}
            {value!.country && value!.country !== value!.name && `, ${value!.country}`}
          </span>
        </div>
      )}

      {/* Dropdown */}
      {isOpen && (results.length > 0 || showNoResults) && (
        <ul
          ref={listRef}
          id={listboxId}
          role="listbox"
          aria-label="Place suggestions"
          className={cn(
            "absolute z-50 mt-1 w-full max-h-64 overflow-auto rounded-md border border-neutral-200",
            "bg-white py-1 shadow-lg",
            "scrollbar-thin"
          )}
        >
          {showNoResults ? (
            <li className="px-3 py-3 text-sm text-neutral-500 text-center">
              No places found for "{query}"
            </li>
          ) : (
            results.map((place, index) => {
              const subLabel = buildSubLabel(place);
              const isActive = activeIndex === index;
              return (
                <li
                  key={`${place.place_id}-${index}`}
                  id={`${listboxId}-option-${index}`}
                  role="option"
                  aria-selected={isActive}
                  className={cn(
                    "flex cursor-pointer items-start gap-3 px-3 py-2.5 text-sm transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-900"
                      : "text-neutral-800 hover:bg-neutral-50"
                  )}
                  onMouseDown={(e) => {
                    e.preventDefault(); // Prevent input blur before selection
                    handleSelect(place);
                  }}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  {/* Flag */}
                  <span className="mt-0.5 text-base leading-none shrink-0" aria-hidden="true">
                    {countryFlag(place.country_code)}
                  </span>

                  {/* Labels */}
                  <div className="flex flex-col min-w-0">
                    <span className="font-medium truncate leading-tight">{place.name}</span>
                    {subLabel && (
                      <span className="text-xs text-neutral-500 truncate leading-tight mt-0.5">
                        {subLabel}
                      </span>
                    )}
                    {place.place_type && (
                      <span className="text-[10px] text-neutral-400 mt-0.5 uppercase tracking-wide font-medium">
                        {place.place_type}
                      </span>
                    )}
                  </div>
                </li>
              );
            })
          )}
        </ul>
      )}
    </div>
  );
}
