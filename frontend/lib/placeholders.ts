export const CIVIC_PULSE_PLACEHOLDER_IMAGE =
  "https://placehold.co/1200x675/e2e8f0/334155?text=Civic+Pulse";

export function articleImageUrl(image: string | null | undefined): string {
  return image?.trim() || CIVIC_PULSE_PLACEHOLDER_IMAGE;
}
