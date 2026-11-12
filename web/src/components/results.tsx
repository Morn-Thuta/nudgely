import evidence from "@/data/evidence.json";
import summary from "@/data/summary.json";
const model = evidence.transferable;
export function Results() {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">The difference a nudge makes</p>
          <h1>Evidence before promises.</h1>
          <p>Public experiment results, with the uncertainty kept in view.</p>
        </div>
        <span className="pill">Historical Lenta data</span>
      </div>
      <div className="metric-grid">
        <div className="metric">
          <span>Estimated effect captured by top 30%</span>
          <strong>{Math.round(model.capture_mean * 100)}%</strong>
        </div>
        <div className="metric">
          <span>Compared with random 30%</span>
          <strong>{(model.capture_mean / 0.3).toFixed(1)}×</strong>
        </div>
        <div className="metric">
          <span>Range across seven test splits</span>
          <strong>
            {Math.round(model.capture_min * 100)}–
            {Math.round(model.capture_max * 100)}%
          </strong>
        </div>
      </div>
      <div className="results-grid">
        <section className="panel">
          <p className="eyebrow">Targeting efficiency</p>
          <h2>
            Same audience size.
            <br />A different selection.
          </h2>
          <p>
            Share of the estimated incremental effect captured when selecting
            30% of customers.
          </p>
          <div className="bar-chart">
            {[
              ["Random selection", 30],
              ["Nudgely", model.capture_mean * 100],
            ].map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <div className="bar-track">
                  <div style={{ width: `${value}%` }} />
                </div>
                <strong>{Math.round(Number(value))}%</strong>
              </div>
            ))}
          </div>
          <p className="fine">
            Ten shop-computable features. Mean of seven Lenta splits. The 38–85%
            range is variability across splits, not a confidence interval or
            guaranteed shop result.
          </p>
        </section>
        <section className="panel">
          <p className="eyebrow">The underlying SMS experiment</p>
          <h2>
            A small lift.
            <br />
            Across many customers.
          </h2>
          <div className="rate-pair">
            <div>
              <strong>{(summary.visit_rate_no_msg * 100).toFixed(1)}%</strong>
              <span>No message</span>
            </div>
            <span>→</span>
            <div>
              <strong>{(summary.visit_rate_msg * 100).toFixed(1)}%</strong>
              <span>Received a message</span>
            </div>
          </div>
          <p>
            Visit rates across the full historical Lenta dataset. This does not
            measure our demo campaign.
          </p>
        </section>
      </div>
      <section className="panel">
        <h2>What this evidence doesn’t tell us yet.</h2>
        <div className="feature-grid">
          <div>
            <h3>A local shop’s result</h3>
            <p>
              Lenta is overseas grocery data. A Singapore pilot needs consent, a
              comparison group and observed return visits.
            </p>
          </div>
          <div>
            <h3>The effect on lapsed customers</h3>
            <p>
              The model lacks a direct recency feature. Its weak handling of
              lapsed customers is a known limitation.
            </p>
          </div>
          <div>
            <h3>Live campaign outcomes</h3>
            <p>
              No live campaign outcomes are shown here. Return visits still need
              to be matched to a real campaign and its comparison group.
            </p>
          </div>
        </div>
        <a
          className="text-link"
          href="https://github.com/Morn-Thuta/nudgely/blob/main/docs/Numbers.md"
        >
          Read the numbers sheet and methodology ↗
        </a>
      </section>
    </>
  );
}
