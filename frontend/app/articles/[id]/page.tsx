import Link from "next/link";
import { notFound } from "next/navigation";
import { getArticle } from "@/lib/api";

export const dynamic = "force-dynamic";

type ArticlePageProps = {
  params: Promise<{
    id: string;
  }>;
};

function paragraphs(text: string): string[] {
  return text
    .split(/\n{2,}/)
    .map((part) => part.trim())
    .filter(Boolean);
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const { id } = await params;
  const article = await getArticle(id).catch(() => null);

  if (!article) {
    notFound();
  }

  return (
    <main className="page">
      <article className="article-page">
        <Link className="back-link" href="/">
          Back to latest briefs
        </Link>
        <div className="source-line">{article.source}</div>
        <h1>{article.title}</h1>
        <div className="meta">{article.date}</div>

        {article.image ? (
          <div className="lead-image">
            <img alt="" src={article.image} />
          </div>
        ) : null}

        <section className="article-body" aria-label="Summary">
          <p>
            <strong>Summary: </strong>
            {article.summary}
          </p>
        </section>

        <section className="article-body" aria-label="Full text">
          {paragraphs(article.full_text).map((paragraph, index) => (
            <p key={`${article.id}-${index}`}>{paragraph}</p>
          ))}
        </section>
      </article>
    </main>
  );
}
