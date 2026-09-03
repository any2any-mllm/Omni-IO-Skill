# Scenario Template: [Scenario Name]

## Scenario Description

[Describe the scenario's typical user needs and use cases in one or two sentences.]

---

## Trigger Examples

Possible user inputs (illustrative, not exhaustive):

- "[Example input 1]"
- "[Example input 2]"
- "[Example input 3]"

---

## Trigger Boundary

**Trigger when:** [The user explicitly requests a bundle of multiple deliverables, or the request conventionally implies a complete package for this scenario.]

**Do not trigger when:** [The user requests only one type of asset involved in the scenario. Use the corresponding atomic skill and do not add deliverables the user did not request.]

**When uncertain:** Ask the user to confirm the deliverable scope instead of assuming the complete scenario package.

---

## Typical Input Assets

| Asset Type | Description | Required? |
|------------|-------------|-----------|
| [Type] | [Description] | Required / Optional |

---

## Media and Deliverable Selection Rules

This section, rather than a fixed chain, is the core of a Scenario skill. In most scenarios, the required deliverables, whether an Expert is needed, and which atomic skills to use depend on the specific request; do not predetermine a fixed package. Evaluate in this order:

1. **Prioritize modalities and deliverable types the user explicitly mentions**, such as video, image, music, or report.
2. **When the user is not specific, use common conventions for this scenario:** [List practical defaults based on platform, audience, or purpose when the request is incomplete.] If the conventional choice remains uncertain, follow the Trigger Boundary and ask rather than assuming.
3. **Choose an execution layer for each deliverable:** Use the corresponding Expert for one complete, professional output that requires multi-step assembly and final review. Use an atomic skill when one call is sufficient.
4. **Dependencies between atomic skills still follow `orchestration/dependency_rules.md`.** Declare `depends_on` according to which downstream task genuinely consumes which upstream output.
5. The decision determines the number and types of tasks; do not assume a fixed count. The result may require one atomic skill or a combination of several.

---

## Expert / Atomic Selection Rules

Using `orchestration/expert_protocol.md`, define the selection boundary for this Scenario:

| Deliverable Condition | Execution Method |
|-----------------------|------------------|
| [A final output requiring a complete professional workflow, assembly, and review] | Load `[Expert path]` |
| [A simple asset satisfied by one generation] | Load `[atomic skill path]` directly |

The Scenario declares only the selection rules and how other deliverables reuse an Expert's final output. Do not copy the Expert's detailed internal workflow. After loading, the Expert expands its workflow into existing atomic tasks, which are merged with other Scenario tasks in one `<declare>` graph.

---

## Non-Tool Outputs (If Applicable)

If some Scenario deliverables are **plain text** that Claude generates directly without a `generate_*` MCP tool, such as copy, summaries, or explanations, state here that **these outputs use no tool, create no file, and are not written to the asset registry**. They are part of the response and are presented with the media assets. Delete this section if the Scenario has no such outputs.

**Distinguish carefully:** If Claude natively creates a **real file**, such as code or a webpage, it follows `skills/generate/code.md`, not this section. Call `register_asset()` so the file enters the asset registry and can be referenced in later turns. This section covers only text that remains in the response and is not saved as a file.

---

## Reference `declare` Block

The media and deliverable mix is usually flexible. The following is a **representative example**; adjust the actual task dynamically using the selection rules above rather than copying it as a fixed template:

```
<declare>
{
  "tasks": [
    {
      "id": "[task_id]",
      "type": "[type]",
      "prompt": "[Complete, self-contained description including the scene's atmosphere and modality-specific details]",
      "params": { "[param]": "[value]" }
    },
    {
      "id": "[task_id]",
      "type": "[type]",
      "prompt": "[Complete, self-contained description including the scene's atmosphere and modality-specific details]",
      "depends_on": "[upstream_task_id]"
    }
  ]
}
</declare>
```

Non-tool outputs, if any, do not appear in the `declare` block.

---

## Expected Outputs

| Asset Type | Description |
|------------|-------------|
| [Type] | [Description] |

---

## Extensions

- [Optional extra task or variant]
- [Common follow-on need for this Scenario]
