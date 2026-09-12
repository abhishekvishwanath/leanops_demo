export function LoadingState({ label = "Loading..." }) {
  return <div className="text-sm text-slate-500 py-8 text-center">{label}</div>;
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 text-red-800 text-sm p-4 my-4">
      <div className="font-medium mb-1">Couldn&apos;t load data</div>
      <div className="mb-2">{String(error?.message || error)}</div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded bg-red-600 text-white text-xs px-2 py-1 hover:bg-red-700"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ label = "Nothing here yet." }) {
  return <div className="text-sm text-slate-400 py-8 text-center">{label}</div>;
}
