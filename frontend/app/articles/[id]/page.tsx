import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, CalendarDays, FileText } from "lucide-react";
import { getArticle } from "@/lib/api";
import { articleImageUrl } from "@/lib/placeholders";

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
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
      <article>
        <Link
          className="inline-flex items-center gap-2 text-sm font-semibold text-sky-800 transition hover:text-sky-950"
          href="/"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          Back to latest briefs
        </Link>

        <header className="mt-6 border-b border-slate-200 pb-8">
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="rounded-full bg-sky-50 px-3 py-1 font-semibold text-sky-800">
              {article.source}
            </span>
            <span className="inline-flex items-center gap-1.5 text-slate-500">
              <CalendarDays aria-hidden="true" className="h-4 w-4" />
              {article.date}
            </span>
          </div>
          <h1 className="mt-5 max-w-4xl text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">
            {article.title}
          </h1>
        </header>

        <div className="mt-8 aspect-[16/9] overflow-hidden rounded-2xl bg-slate-200 shadow-sm">
          <img alt="" className="h-full w-full object-cover" src={articleImageUrl(article.image)} />
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-[240px_minmax(0,1fr)]">
          <aside className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
                  <FileText aria-hidden="true" className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-slate-950">Source brief</p>
                  <p className="text-sm text-slate-500">{article.source}</p>
                </div>
              </div>
            </div>
          </aside>

          <div className="space-y-8">
            <section
              aria-label="Summary"
              className="rounded-2xl border border-sky-100 bg-sky-50 p-6 shadow-sm"
            >
              <h2 className="text-sm font-bold uppercase tracking-wide text-sky-900">Summary</h2>
              <p className="mt-3 text-lg leading-8 text-slate-700">{article.summary}</p>
            </section>

            <section aria-label="Full text" className="space-y-5 text-lg leading-8 text-slate-700">
              {paragraphs(article.full_text).map((paragraph, index) => (
                <p key={`${article.id}-${index}`}>{paragraph}</p>
              ))}
            </section>
          </div>
        </div>
      </article>
    </main>
  );
}
