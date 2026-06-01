export function JsonBlock({ data }: { data: unknown }) {
  return (
    <pre className="json-block">{data == null ? '—' : JSON.stringify(data, null, 2)}</pre>
  );
}
