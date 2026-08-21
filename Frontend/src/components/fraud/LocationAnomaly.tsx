import { Navigation } from "lucide-react";
import { DEMO_LOCATION_EVENT } from "@/lib/fraud/mock";
import { KeyValue, Panel, PanelHeader } from "./primitives";

export function LocationAnomalyCard() {
  const e = DEMO_LOCATION_EVENT;
  return (
    <Panel>
      <PanelHeader
        title="Location Anomaly"
        subtitle="Geo-velocity check on consecutive transactions"
        icon={<Navigation className="h-4 w-4" />}
      />
      <div className="px-5 py-4">
        <div className="relative rounded-lg border border-border bg-muted/40 p-4">
          <svg viewBox="0 0 320 140" className="h-32 w-full">
            <path
              d="M40 30 C 120 10, 220 60, 280 110"
              fill="none"
              stroke="var(--color-critical)"
              strokeWidth="2"
              strokeDasharray="5 4"
            />
            <circle cx="40" cy="30" r="6" fill="var(--color-info)" />
            <circle cx="280" cy="110" r="6" fill="var(--color-critical)" />
            <circle cx="280" cy="110" r="12" fill="var(--color-critical)" opacity="0.18" />
            <text x="54" y="28" fontSize="11" fill="var(--color-muted-foreground)">
              {e.previousLocation}
            </text>
            <text x="196" y="128" fontSize="11" fill="var(--color-muted-foreground)">
              {e.currentLocation}
            </text>
            <text x="130" y="72" fontSize="10" fill="var(--color-critical)">
              ~{e.distanceKm} km / {e.minutesApart} min
            </text>
          </svg>
        </div>
        <div className="mt-3 divide-y divide-border">
          <KeyValue label="Previous Location" value={e.previousLocation} />
          <KeyValue label="Current Location" value={e.currentLocation} tone="critical" />
          <KeyValue label="Distance" value={`~${e.distanceKm} km`} />
          <KeyValue label="Time Difference" value={`${e.minutesApart} minutes`} />
          <KeyValue
            label="Required Travel Speed"
            value={`~${e.requiredSpeedKmh.toLocaleString("en-IN")} km/h`}
            tone="critical"
          />
        </div>
        <div className="mt-3 rounded-lg border border-critical/30 bg-critical-soft px-3 py-2 text-xs font-semibold text-critical">
          IMPOSSIBLE TRAVEL DETECTED
        </div>
        <p className="mt-2 text-[11px] text-muted-foreground">
          Physically unachievable movement between transactions indicates possible credential or
          account compromise.
        </p>
      </div>
    </Panel>
  );
}
