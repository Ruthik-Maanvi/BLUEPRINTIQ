import UploadZone from "@/components/UploadZone";

export default function UploadPage() {
  return (
    <div className="flex flex-col gap-8 max-w-2xl mx-auto mt-12">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-blueprint-100">Upload Project</h1>
        <p className="text-blueprint-400">
          Ingest documents to generate structured procurement intelligence.
        </p>
      </header>
      
      {/* This renders the actual drag-and-drop box you built earlier */}
      <UploadZone />
    </div>
  );
}