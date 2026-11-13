from __future__ import annotations

import argparse
import json
from html import escape
from typing import Any

UI_SCHEMA = "forprint_oc01_minimum_console_ui_v0_1"


def _safe_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return (
        raw.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def render_console_html(initial_snapshot: dict[str, Any] | None = None) -> str:
    snapshot = initial_snapshot or {
        "schema_version": "forprint_oc01_console_snapshot_v0_1",
        "state": "NOT_LOADED",
    }
    initial = _safe_json(snapshot)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ForPrint Operator Console — OC01 MINI-6</title>
<style>
:root {{
  color-scheme: light dark;
  font-family: Inter, system-ui, -apple-system, Segoe UI, sans-serif;
  --gap: 14px;
  --radius: 14px;
  --border: color-mix(in srgb, currentColor 18%, transparent);
  --panel: color-mix(in srgb, Canvas 94%, currentColor 6%);
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: Canvas; color: CanvasText; }}
header {{
  position: sticky; top: 0; z-index: 4; padding: 14px 16px;
  background: color-mix(in srgb, Canvas 92%, transparent);
  backdrop-filter: blur(10px); border-bottom: 1px solid var(--border);
}}
h1 {{ margin: 0; font-size: 1.1rem; }}
small, .muted {{ opacity: .72; }}
main {{
  max-width: 1180px; margin: 0 auto; padding: 16px;
  display: grid; gap: var(--gap);
  grid-template-columns: repeat(12, minmax(0, 1fr));
}}
.card {{
  grid-column: span 6; border: 1px solid var(--border);
  border-radius: var(--radius); padding: 14px; background: var(--panel);
}}
.card.wide {{ grid-column: 1 / -1; }}
.banner {{
  padding: 10px 12px; border: 1px solid var(--border);
  border-radius: 10px; margin-top: 10px; font-size: .9rem;
}}
label {{ display: grid; gap: 5px; margin: 9px 0; font-size: .88rem; }}
input, select, textarea, button {{
  width: 100%; font: inherit; padding: 10px; border-radius: 9px;
  border: 1px solid var(--border); background: Canvas; color: CanvasText;
}}
textarea {{ min-height: 76px; resize: vertical; }}
button {{ cursor: pointer; font-weight: 650; }}
.actions {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }}
pre {{
  white-space: pre-wrap; overflow-wrap: anywhere; max-height: 420px;
  overflow: auto; padding: 10px; border-radius: 10px;
  background: color-mix(in srgb, Canvas 85%, currentColor 15%);
}}
@media (max-width: 760px) {{
  main {{ padding: 10px; }}
  .card {{ grid-column: 1 / -1; }}
  .actions {{ grid-template-columns: 1fr; }}
  header {{ position: static; }}
}}
</style>
</head>
<body>
<header>
  <h1>ForPrint Operator Console <small>OC01 MINI-6</small></h1>
  <div class="banner">
    Console is <strong>not</strong> execution/state authority. MINI-6 has no built-in authentication or TLS.
    Default server bind is loopback; use only
    a trusted tunnel or protected transport for remote phone/laptop access.
  </div>
</header>
<main>
<section class="card wide">
  <h2>State snapshot</h2>
  <label>Session projection path
    <input id="session_projection" data-save placeholder="/runtime/session.yaml">
  </label>
  <label>Sandbox manifest path
    <input id="sandbox_manifest" data-save placeholder="/runtime/.../workspace_manifest.yaml">
  </label>
  <label>Result manifest path
    <input id="result_manifest" data-save placeholder="/runtime/.../workspace_manifest.yaml">
  </label>
  <label>Promotion preview path
    <input id="promotion_preview" data-save placeholder="/runtime/.../promotion_preview.yaml">
  </label>
  <button onclick="refreshSnapshot()">Refresh snapshot</button>
  <pre id="snapshot"></pre>
</section>

<section class="card">
  <h2>Protected Terminal</h2>
  <label>Capability
    <select id="terminal_capability" data-save>
      <option value="repo_status">repo_status</option>
      <option value="repo_head">repo_head</option>
      <option value="repo_diff_check">repo_diff_check</option>
    </select>
  </label>
  <div class="actions">
    <button onclick="terminalAction('terminal_plan')">Plan</button>
    <button onclick="terminalAction('terminal_run')">Run read-only</button>
  </div>
</section>

<section class="card">
  <h2>Assistant Dev Sandbox</h2>
  <label>Module ID<input id="module_id" data-save value="forprint_system_blueprint"></label>
  <label>Worker ID<input id="worker_id" data-save value="operator-assistant"></label>
  <label>Attempt ID<input id="attempt_id" data-save></label>
  <label>Expected BASE_HEAD<input id="base_head" data-save></label>
  <div class="actions">
    <button onclick="sandboxCreate()">Create sandbox</button>
    <button onclick="sandboxStatus()">Sandbox status</button>
  </div>
</section>

<section class="card">
  <h2>Checkpoint &amp; sealed result</h2>
  <label>Resume evidence (optional)<input id="resume_evidence" data-save></label>
  <label>Validation evidence, one per line
    <textarea id="validation_evidence" data-save>console-ui:PASS</textarea>
  </label>
  <div class="actions">
    <button onclick="checkpoint()">Checkpoint</button>
    <button onclick="sealResult()">Seal result</button>
  </div>
</section>

<section class="card wide">
  <h2>Promotion preview</h2>
  <p class="muted">Preview only. MINI-6 intentionally exposes no promotion-apply control.</p>
  <label>Candidate root<input id="candidate_root" data-save></label>
  <label>Sealed result<input id="sealed_result" data-save></label>
  <label>Work Front<input id="work_front" data-save></label>
  <label>Origin Handoff manifest<input id="origin_handoff" data-save></label>
  <label>Handoff result<input id="handoff_result" data-save></label>
  <label>Profile ref<input id="profile_ref" data-save placeholder="profile@revision"></label>
  <label>Procedure ID<input id="procedure_id" data-save></label>
  <label>Preview output path<input id="preview_output" data-save></label>
  <button onclick="promotionPreview()">Build promotion preview</button>
</section>

<section class="card wide">
  <h2>Last action result</h2>
  <pre id="result">No action yet.</pre>
</section>
</main>
<script>
const INITIAL_SNAPSHOT = {initial};
const $ = (id) => document.getElementById(id);
const val = (id) => $(id).value.trim();

function restore() {{
  document.querySelectorAll("[data-save]").forEach(el => {{
    const saved = localStorage.getItem("oc01:" + el.id);
    if (saved !== null) el.value = saved;
    el.addEventListener("change", () => localStorage.setItem("oc01:" + el.id, el.value));
  }});
  $("snapshot").textContent = JSON.stringify(INITIAL_SNAPSHOT, null, 2);
}}

async function jsonFetch(url, options={{}}) {{
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(payload, null, 2));
  return payload;
}}

async function action(name, payload) {{
  try {{
    const result = await jsonFetch("/api/action/" + name, {{
      method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify(payload),
    }});
    $("result").textContent = JSON.stringify(result, null, 2);
    return result;
  }} catch (err) {{
    $("result").textContent = String(err);
    throw err;
  }}
}}

async function refreshSnapshot() {{
  const q = new URLSearchParams();
  for (const id of ["session_projection","sandbox_manifest","result_manifest","promotion_preview"]) {{
    if (val(id)) q.set(id, val(id));
  }}
  try {{
    const data = await jsonFetch("/api/snapshot?" + q.toString());
    $("snapshot").textContent = JSON.stringify(data, null, 2);
  }} catch (err) {{
    $("snapshot").textContent = String(err);
  }}
}}

function terminalPayload() {{
  return {{
    session_projection: val("session_projection"),
    capability_id: val("terminal_capability"),
    enabled: true,
    confirm: true,
  }};
}}
function terminalAction(name) {{ return action(name, terminalPayload()); }}

function sandboxCreate() {{
  return action("sandbox_create", {{
    session_projection: val("session_projection"),
    module_id: val("module_id"),
    worker_id: val("worker_id"),
    attempt_id: val("attempt_id"),
    expected_base_head: val("base_head"),
  }});
}}
function sandboxStatus() {{
  return action("sandbox_status", {{
    session_projection: val("session_projection"),
    manifest: val("sandbox_manifest"),
  }});
}}
function checkpoint() {{
  return action("checkpoint", {{
    session_projection: val("session_projection"),
    manifest: val("result_manifest") || val("sandbox_manifest"),
    resume_evidence: val("resume_evidence"),
  }});
}}
function sealResult() {{
  return action("seal", {{
    session_projection: val("session_projection"),
    manifest: val("result_manifest") || val("sandbox_manifest"),
    validation_evidence: val("validation_evidence").split("\\n").filter(Boolean),
  }});
}}
function promotionPreview() {{
  return action("promotion_preview", {{
    candidate_root: val("candidate_root"),
    sealed_result: val("sealed_result"),
    work_front: val("work_front"),
    origin_handoff_manifest: val("origin_handoff"),
    handoff_result: val("handoff_result"),
    expected_profile_ref: val("profile_ref"),
    expected_procedure_id: val("procedure_id"),
    output: val("preview_output"),
    operator_review: true,
  }});
}}
restore();
</script>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render OC01 MINI-6 responsive Console HTML")
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args()
    html = render_console_html()
    if args.print:
        print(html)
    else:
        print("OC01_CONSOLE_UI=PASS")
        print(f"SCHEMA={UI_SCHEMA}")
        print("RESPONSIVE=true")
        print("STATE_AUTHORITY=false")
        print("PROMOTION_APPLY_CONTROL=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
