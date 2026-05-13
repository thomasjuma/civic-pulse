import type { Article } from "@/types/article";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type SubscriberPayload = {
  email: string;
  whatsapp_number: string;
  has_whatsapp_consent: boolean;
};

export type Subscriber = SubscriberPayload & {
  id: number;
  clerk_user_id: string | null;
  consented_at: string | null;
};

export async function getArticles(): Promise<Article[]> {
  const response = await fetch(`${API_BASE_URL}/articles`, {
    next: { revalidate: 60 },
  });

  if (!response.ok) {
    throw new Error("Unable to load articles");
  }

  return response.json();
}

export async function getArticle(id: string): Promise<Article> {
  const response = await fetch(`${API_BASE_URL}/articles/${id}`, {
    next: { revalidate: 60 },
  });

  if (!response.ok) {
    throw new Error("Unable to load article");
  }

  return response.json();
}

export async function subscribeToUpdates(payload: SubscriberPayload): Promise<Subscriber> {
  const response = await fetch(`${API_BASE_URL}/subscribers`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Unable to save subscription");
  }

  return response.json();
}
