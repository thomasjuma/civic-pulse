import Link from "next/link";
import { getArticles } from "@/lib/api";
import type { Article } from "@/types/article";

export const dynamic = "force-dynamic";

function articleImage(article: Article) {
  if (!article.image) {
    return null;
  }

  return (
    <div className="article-image">
      <img alt="" src={article.image} />
    </div>
  );
}

export default async function Home() {
  const articles = await getArticles().catch(() => []);
  const [leadArticle, ...otherArticles] = articles;

  return (
    <main className="page">
      <div className="section-rule">
        <h1>Latest Civic Briefs</h1>
        <span className="meta">Last five generated summaries</span>
      </div>

      {!leadArticle ? (
        <section className="empty-state">
          <h2>No generated summaries yet</h2>
          <p>
            Run the scheduled ingestion job or trigger the backend ingestion endpoint to
            populate Civic Pulse with the latest source summaries.
          </p>
        </section>
      ) : (
        <section className="article-grid">
          <Link className="lead-story" href={`/articles/${leadArticle.id}`}>
            {articleImage(leadArticle)}
            <div className="source-line">{leadArticle.source}</div>
            <h2>{leadArticle.title}</h2>
            <p className="summary">{leadArticle.summary}</p>
            <div className="meta">{leadArticle.date}</div>
          </Link>

          <div className="article-list">
            {otherArticles.map((article) => (
              <Link className="story-card" href={`/articles/${article.id}`} key={article.id}>
                <div className="source-line">{article.source}</div>
                <h2>{article.title}</h2>
                <p>{article.summary}</p>
                <div className="meta">{article.date}</div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
