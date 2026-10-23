# TC-<AREA>-<NNN> — Title

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

What the case demonstrates.

## Test level and type

Level: hardware validation, software component on the Raspberry Pi,
integration, or simulated end-to-end.

Type: functional, negative, or measurement. A case may combine them.

## Requirements and ClickUp traceability

- ClickUp: task link, or "none", or "PENDING CLICKUP TASK CREATION".
- Requirement: one or two sentences.

## Source modules and documentation

- Modules: `package.module` paths.
- Documents: relative links.

## Preconditions and dependencies

- Earlier cases that must already have an execution, or "none".
- Configuration that must already be true.
- Processes that must be stopped so they do not hold a device.

## Required hardware and software

- Board, PC, button, microphone, cables.
- Commands and packages the procedure uses.
- Privileges (`sudo` or group membership), if any.

## Preparation

1. Steps that do not yet collect pass/fail samples.

## Execution

1. Numbered actions.
2. Commands in fenced blocks.
3. Placeholders written as `<name>` and defined in the same case.

## Observations and evidence

- What the operator writes down.
- Evidence ids and checksums.
- Raw table columns.

## Metrics

- Name, unit, instrument, and whether a limit is **TO BE DEFINED** or
  **NOT MEASURED**.

## Acceptance criteria

- Each criterion is something a later reader can mark pass or fail without
  interpreting a feeling.
- Criteria that are not yet numeric say so.

## Failure conditions

- Product failures.
- Conditions that are **BLOCKED** instead of **FAILED**.

## Recovery and cleanup

1. Stop processes.
2. Leave the device safe.
3. Do not "fix" a failure inside the same execution and then mark it passed.

## Limitations and exclusions

- What a pass does not prove.
