interface Props {
  params: Promise<{ id: string; panel: string }>;
}

export default async function PanelPage({ params }: Props) {
  const { id, panel } = await params;

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold capitalize mb-1">{panel}</h1>
      <p className="text-sm text-muted-foreground">{id}</p>
    </div>
  );
}
