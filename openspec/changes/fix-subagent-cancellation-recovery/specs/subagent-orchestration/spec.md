# Subagent Orchestration

## ADDED Requirements

### Requirement: Cancellation Recovery

The system SHALL recover completed work from cancelled subagents by reading the subagent's workspace before returning a cancellation response. This follows the same graceful selection pattern used by the orchestrator's `_handle_orchestrator_timeout()`.

#### Scenario: Subagent cancelled after full completion (presentation phase)
- **GIVEN** a subagent's `status.json` has `coordination.phase` set to `presentation`
- **AND** `results.winner` identifies the winning agent
- **WHEN** the subagent is cancelled due to timeout
- **THEN** the system SHALL extract the winner's answer from the workspace
- **AND** the status SHALL be `completed_but_timeout`
- **AND** the `success` field SHALL be `true`

#### Scenario: Subagent cancelled during voting (enforcement phase)
- **GIVEN** a subagent's `status.json` has `coordination.phase` set to `enforcement`
- **AND** at least one agent has submitted an answer
- **WHEN** the subagent is cancelled due to timeout
- **THEN** the system SHALL select an answer using the same logic as `_determine_final_agent_from_votes()` (most votes, ties broken by registration order)
- **AND** the status SHALL be `partial`

#### Scenario: Subagent cancelled with answers but no votes
- **GIVEN** a subagent's `status.json` has agents with answers but no votes recorded
- **WHEN** the subagent is cancelled due to timeout
- **THEN** the system SHALL return the first registered agent's answer
- **AND** the status SHALL be `partial`

#### Scenario: Subagent cancelled with no recoverable answer
- **GIVEN** a subagent has no `status.json` or no agents have submitted answers
- **WHEN** the subagent is cancelled due to timeout
- **THEN** the system SHALL return `timeout` status with `answer: null`
- **AND** the `success` field SHALL be `false`
- **AND** the `workspace_path` SHALL still be provided so the parent agent can inspect partial work

### Requirement: Workspace Access

The system SHALL always provide the workspace path in cancellation responses, regardless of whether an answer was recovered. This enables parent agents to inspect logs, partial files, and debug information.

#### Scenario: Workspace path always returned
- **GIVEN** a subagent was spawned and created a workspace
- **WHEN** the subagent is cancelled for any reason (timeout, error, cancellation)
- **THEN** the response SHALL include `workspace_path` pointing to the subagent's workspace directory

#### Scenario: Parent agent can read workspace files
- **GIVEN** a subagent returned with `answer: null` but `workspace_path` is set
- **WHEN** the parent agent uses filesystem tools to read files in the workspace
- **THEN** the parent agent SHALL be able to access any files created by the subagent

### Requirement: Token Usage Preservation

The system SHALL always return accurate token usage for cancelled subagents by reading cost data from the workspace's `status.json`.

#### Scenario: Token usage extracted from status.json
- **GIVEN** a subagent's `status.json` has `costs.total_input_tokens`, `costs.total_output_tokens`, and `costs.total_estimated_cost`
- **WHEN** the subagent is cancelled
- **THEN** the response SHALL include `token_usage` with `input_tokens`, `output_tokens`, and `estimated_cost` populated from the status file

#### Scenario: No cost data available
- **GIVEN** a subagent has no `status.json` or no `costs` section
- **WHEN** the subagent is cancelled
- **THEN** the response SHALL include empty `token_usage: {}`

### Requirement: Completion Percentage Reporting

The system SHALL include completion percentage in cancellation responses when available from the subagent's `status.json`.

#### Scenario: Completion percentage available
- **GIVEN** a subagent's `status.json` has `coordination.completion_percentage`
- **WHEN** the subagent is cancelled
- **THEN** the response SHALL include `completion_percentage` field with the value from status.json

#### Scenario: Completion percentage unavailable
- **GIVEN** a subagent has no `coordination.completion_percentage` in `status.json`
- **WHEN** the subagent is cancelled
- **THEN** the response SHALL omit the `completion_percentage` field
