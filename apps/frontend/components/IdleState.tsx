export function IdleState() {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center text-center">
      <div className="mb-3 text-5xl text-slate-700">▦</div>
      <h2 className="text-lg font-semibold text-slate-300">No ticker watched</h2>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        Enter a ticker above and click <span className="text-slate-300">Watch</span> to see its
        live tape read — quote, recent trades, the core features, the current tape state and
        confidence, observations, and the event log.
      </p>
      <p className="mt-4 font-mono text-xs text-slate-600">Try: SIM-BUYER</p>
    </div>
  );
}

// Pending/connecting cockpit treatment (J-21): shown the instant Watch is clicked, before any
// tape data. When a symbol is supplied it is named explicitly ("Connecting to <SYMBOL>…") so the
// click is acknowledged distinctly per symbol; the amber pulsing dot mirrors CONN_DOT.connecting.
export function ConnectingState({ symbol }: { symbol?: string }) {
  return (
    <div
      className="flex min-h-[40vh] flex-col items-center justify-center text-center"
      aria-live="polite"
      data-testid="connecting-state"
    >
      <div className="mb-3 h-3 w-3 animate-pulse rounded-full bg-amber-400" />
      <p className="text-sm text-slate-400">
        {symbol ? (
          <>
            Connecting to <span className="font-mono text-slate-200">{symbol}</span>…
          </>
        ) : (
          "Connecting to the tape stream…"
        )}
      </p>
    </div>
  );
}

// Surfaced connect-failure cockpit treatment (J-23): rendered in place of the cockpit when the
// initial snapshot fetch or the WS failed before any frame arrived — an explicit, distinct state
// (never a frozen "Connecting…" and never a fabricated cockpit). Rose = failure, per the palette.
export function StreamFailedState({ message }: { message?: string }) {
  return (
    <div
      className="flex min-h-[40vh] flex-col items-center justify-center text-center"
      role="alert"
      data-testid="stream-failed-state"
    >
      <div className="mb-3 text-4xl text-rose-400" aria-hidden="true">
        ⚠
      </div>
      <h2 className="text-lg font-semibold text-rose-300">Couldn’t connect to the tape stream</h2>
      <p className="mt-2 max-w-md text-sm text-slate-400">
        {message ?? "Couldn’t connect to the tape stream."} The backend may be unreachable or the
        request timed out. No tape is shown — Tapeology never fabricates data. Try Watch again.
      </p>
    </div>
  );
}
