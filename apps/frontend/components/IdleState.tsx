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

export function ConnectingState() {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center text-center">
      <div className="mb-3 h-3 w-3 animate-pulse rounded-full bg-amber-400" />
      <p className="text-sm text-slate-500">Connecting to the tape stream…</p>
    </div>
  );
}
