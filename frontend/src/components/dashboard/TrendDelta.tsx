import { TrendingUp } from "lucide-react";

interface TrendDeltaProps {
  delta: number;
}

export function TrendDelta({ delta }: TrendDeltaProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-800">
      <TrendingUp className="h-3.5 w-3.5" aria-hidden />
      +{delta}/24h
    </span>
  );
}
