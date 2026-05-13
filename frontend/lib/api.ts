import type { Article } from "@/types/article";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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

