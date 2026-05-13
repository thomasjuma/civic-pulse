import Link from "next/link";
import { ArrowUpRight, CalendarDays, FileText, Newspaper } from "lucide-react";
import { SubscribeForm } from "@/components/SubscribeForm";
import { getArticles } from "@/lib/api";
import { articleImageUrl } from "@/lib/placeholders";
import type { Article } from "@/types/article";

export const dynamic = "force-dynamic";

function articleImage(article: Article) {
  return (
    <div className="aspect-[16/9] overflow-hidden bg-slate-200">
      <img
        alt=""
        className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
        src={articleImageUrl(article.image)}
      />
    </div>
  );
}

export default async function Home() {
  const articles = await getArticles().catch(() => []);
  const [leadArticle, ...otherArticles] = articles;

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
      <section className="mb-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-end">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-sm font-semibold text-sky-800">
            <Newspaper aria-hidden="true" className="h-4 w-4" />
            Civic Pulse Digest
          </div>
          <h1 className="mt-4 max-w-3xl text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">
            Latest civic briefs
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
            Professional summaries of public reports, bills, and acts prepared for
            clearer citizen participation.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
              <FileText aria-hidden="true" className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-950">Last five summaries</p>
              <p className="text-sm text-slate-500">Updated from generated article records</p>
            </div>
          </div>
        </div>
      </section>

      <SubscribeForm />

      {!leadArticle ? (
        <section className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
            <FileText aria-hidden="true" className="h-6 w-6" />
          </div>
          <h2 className="mt-4 text-xl font-bold text-slate-950">No generated summaries yet</h2>
          <p className="mx-auto mt-2 max-w-2xl text-slate-600">
            Run the scheduled ingestion job or trigger the backend ingestion endpoint to
            populate Civic Pulse with the latest source summaries.
          </p>
        </section>
      ) : (
        <section className="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
          <Link
            className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-xl"
            href={`/articles/${leadArticle.id}`}
          >
            {articleImage(leadArticle)}
            <div className="p-6 sm:p-7">
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <span className="rounded-full bg-sky-50 px-3 py-1 font-semibold text-sky-800">
                  {leadArticle.source}
                </span>
                <span className="inline-flex items-center gap-1.5 text-slate-500">
                  <CalendarDays aria-hidden="true" className="h-4 w-4" />
                  {leadArticle.date}
                </span>
              </div>
              <h2 className="mt-4 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
                {leadArticle.title}
              </h2>
              <p className="mt-4 text-base leading-7 text-slate-600">{leadArticle.summary}</p>
              <span className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-sky-800">
                Read full brief
                <ArrowUpRight aria-hidden="true" className="h-4 w-4" />
              </span>
            </div>
          </Link>

          <div className="space-y-4">
            {otherArticles.map((article) => (
              <Link
                className="group block rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-lg"
                href={`/articles/${article.id}`}
                key={article.id}
              >
                <div className="mb-4 aspect-[16/9] overflow-hidden rounded-xl bg-slate-200">
                  <img
                    alt=""
                    className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                    src={articleImageUrl(article.image)}
                  />
                </div>
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="text-xs font-bold uppercase tracking-wide text-sky-800">
                      {article.source}
                    </div>
                    <h2 className="mt-2 text-xl font-bold leading-snug text-slate-950">
                      {article.title}
                    </h2>
                  </div>
                  <ArrowUpRight
                    aria-hidden="true"
                    className="mt-1 h-4 w-4 flex-none text-slate-400 transition group-hover:text-sky-700"
                  />
                </div>
                <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-600">
                  {article.summary}
                </p>
                <div className="mt-4 inline-flex items-center gap-1.5 text-sm text-slate-500">
                  <CalendarDays aria-hidden="true" className="h-4 w-4" />
                  {article.date}
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
