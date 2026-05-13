"use client";

import { FormEvent, useEffect, useState } from "react";
import { Bell, Mail, Phone, ShieldCheck, X } from "lucide-react";
import { subscribeToUpdates } from "@/lib/api";

const SUBSCRIPTION_STATE_KEY = "civic_pulse_subscription_prompt";

type FormState = "idle" | "submitting" | "success" | "error";

export function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [whatsappNumber, setWhatsappNumber] = useState("");
  const [hasConsent, setHasConsent] = useState(false);
  const [formState, setFormState] = useState<FormState>("idle");
  const [message, setMessage] = useState("");
  const [isVisible, setIsVisible] = useState(false);
  const isComplete = formState === "success";
  const isSubmitting = formState === "submitting";
  const isFormLocked = isSubmitting || isComplete;

  useEffect(() => {
    const savedState = window.localStorage.getItem(SUBSCRIPTION_STATE_KEY);
    setIsVisible(savedState !== "subscribed" && savedState !== "dismissed");
  }, []);

  useEffect(() => {
    if (!isVisible) {
      return undefined;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSubmitting) {
        handleDismiss();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSubmitting, isVisible]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!email.trim() || !whatsappNumber.trim()) {
      setFormState("error");
      setMessage("Email and WhatsApp number are required to subscribe.");
      return;
    }

    if (!hasConsent) {
      setFormState("error");
      setMessage("Please consent to receive WhatsApp summaries before subscribing.");
      return;
    }

    setFormState("submitting");
    setMessage("");

    try {
      await subscribeToUpdates({
        email: email.trim(),
        whatsapp_number: whatsappNumber.trim(),
        has_whatsapp_consent: hasConsent,
      });
    } catch {
      setFormState("error");
      setMessage("We could not save your subscription. Please try again.");
      return;
    }

    window.localStorage.setItem(SUBSCRIPTION_STATE_KEY, "subscribed");
    setFormState("success");
    setMessage("Subscription saved. You will receive WhatsApp summaries when new documents are processed.");
    setIsVisible(false);
  }

  function handleDismiss() {
    window.localStorage.setItem(SUBSCRIPTION_STATE_KEY, "dismissed");
    setIsVisible(false);
  }

  if (!isVisible) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6 backdrop-blur-sm sm:px-6">
      <section
        aria-labelledby="subscribe-modal-title"
        aria-modal="true"
        className="w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-slate-900/10"
        role="dialog"
      >
        <div className="flex items-start justify-between gap-5 border-b border-slate-200 px-6 py-5">
          <div className="flex items-start gap-4">
            <span className="flex h-11 w-11 flex-none items-center justify-center rounded-xl bg-sky-50 text-sky-800">
              <Bell aria-hidden="true" className="h-5 w-5" />
            </span>
            <div>
              <div className="text-xs font-bold uppercase tracking-wide text-sky-800">Updates</div>
              <h2 id="subscribe-modal-title" className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
                Receive new civic summaries
              </h2>
            </div>
          </div>

          <button
            aria-label="Close subscription prompt"
            className="inline-flex h-9 w-9 flex-none items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:border-slate-300 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isSubmitting}
            onClick={handleDismiss}
            type="button"
          >
            <X aria-hidden="true" className="h-4 w-4" />
          </button>
        </div>

        <div className="px-6 py-5">
          <p className="text-sm leading-6 text-slate-600">
            Subscribe with your email and WhatsApp number to receive summaries after new
            public documents are processed.
          </p>

          <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="text-sm font-semibold text-slate-800">Email</span>
              <span className="mt-2 flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm focus-within:border-sky-500 focus-within:ring-4 focus-within:ring-sky-100">
                <Mail aria-hidden="true" className="h-4 w-4 flex-none text-slate-400" />
                <input
                  autoComplete="email"
                  className="min-w-0 flex-1 border-0 bg-transparent text-sm text-slate-950 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
                  disabled={isFormLocked}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="reader@example.com"
                  type="email"
                  value={email}
                />
              </span>
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-slate-800">WhatsApp number</span>
              <span className="mt-2 flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm focus-within:border-sky-500 focus-within:ring-4 focus-within:ring-sky-100">
                <Phone aria-hidden="true" className="h-4 w-4 flex-none text-slate-400" />
                <input
                  autoComplete="tel"
                  className="min-w-0 flex-1 border-0 bg-transparent text-sm text-slate-950 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
                  disabled={isFormLocked}
                  onChange={(event) => setWhatsappNumber(event.target.value)}
                  placeholder="254700000000"
                  type="tel"
                  value={whatsappNumber}
                />
              </span>
            </label>

            <label className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
              <input
                checked={hasConsent}
                className="mt-1 h-4 w-4 rounded border-slate-300 text-sky-700 focus:ring-sky-600 disabled:cursor-not-allowed"
                disabled={isFormLocked}
                onChange={(event) => setHasConsent(event.target.checked)}
                type="checkbox"
              />
              <span className="flex gap-2 text-sm leading-6 text-slate-600">
                <ShieldCheck aria-hidden="true" className="mt-0.5 h-4 w-4 flex-none text-sky-800" />
                I consent to receive Civic Pulse summaries on WhatsApp.
              </span>
            </label>

            <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">
              <button
                className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isSubmitting}
                onClick={handleDismiss}
                type="button"
              >
                {isComplete ? "Close" : "Not now"}
              </button>
              <button
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-800 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isFormLocked}
                type="submit"
              >
                <Bell aria-hidden="true" className="h-4 w-4" />
                {isSubmitting ? "Subscribing" : "Subscribe"}
              </button>
            </div>

            {message ? (
              <p
                className={
                  formState === "error"
                    ? "rounded-xl bg-red-50 px-3 py-2 text-sm font-semibold text-red-700"
                    : "rounded-xl bg-sky-50 px-3 py-2 text-sm font-semibold text-sky-800"
                }
              >
                {message}
              </p>
            ) : null}
          </form>
        </div>
      </section>
    </div>
  );
}
