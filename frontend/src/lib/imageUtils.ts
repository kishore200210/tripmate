/**
 * Safely parses and validates an image URL to prevent Next.js <Image> rendering errors.
 * Returns a fallback placeholder if the URL is missing, invalid, or malformed.
 */
export function getSafeImageUrl(url: string | null | undefined): string {
  const FALLBACK_IMAGE = "/globe.svg";

  if (!url || typeof url !== "string" || url.trim() === "") {
    return FALLBACK_IMAGE;
  }

  const trimmedUrl = url.trim();

  // If it's a local static asset, it's safe.
  if (trimmedUrl.startsWith("/")) {
    return trimmedUrl;
  }

  // If it's a data URI, it's safe.
  if (trimmedUrl.startsWith("data:image/")) {
    return trimmedUrl;
  }

  try {
    const parsed = new URL(trimmedUrl);
    // Ensure only http/https protocols are allowed
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return FALLBACK_IMAGE;
    }
    return parsed.href;
  } catch (e) {
    // URL parsing failed, meaning it's an invalid URL structure.
    return FALLBACK_IMAGE;
  }
}
