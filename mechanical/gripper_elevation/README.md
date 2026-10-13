# Gripper Elevation

## Purpose

Investigate positioning a selected manipulation tool relative to the robot.

## Competition Capabilities

Candidate: controlled manipulator positioning. Required task poses and allowable motion need official verification.

## Requirements

TBD: sourced reach/envelope constraints, load cases, positional criteria, retention during motion, and recovery behavior.

## Mechanical Interfaces

TBD: [gripper](../gripper/README.md) attachment, chassis mounts, pose datums, and travel-clearance boundaries.

## Electrical Interfaces

TBD: actuation, position/limit feedback, cable motion allowance, and power needs with [electrical](../../electrical/README.md).

## Software Interfaces

TBD: pose requests, reference/homing semantics, feedback, travel limits, tool interlocks, and fault states.

## Design

Compare positioning architectures based on selected tool loads and verified tasks. Local [cad](cad/README.md) remains separate from [manipulation_system](../assemblies/manipulation_system/README.md) integration references.

## Current Status

Architecture scaffold only; no lift architecture, travel, or actuator selected.

## Testing

Plan positional repeatability, load retention, clearance, and limit/recovery checks after requirements are established.

## Known Issues

TBD: tool choice, task poses, load cases, and reference strategy are unknown.

## Related GitHub Issues

TBD: link actual elevation trade-study and interface issues when created.
