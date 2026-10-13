# Feeder

## Purpose

Investigate controlled ball transfer from storage to shooter.

## Competition Capabilities

Candidate: repeatable ball delivery. Verify applicable handling constraints before choosing a transfer method.

## Requirements

TBD: delivery conditions, isolation needs, sequencing criteria, and jam recovery requirements.

## Mechanical Interfaces

TBD: [storage](../ball_storage/README.md) outlet, [shooter](../shooter/README.md) inlet, and mounting references.

## Electrical Interfaces

TBD: transfer actuation, presence detection, routing, and power allocation with [electrical](../../electrical/README.md).

## Software Interfaces

TBD: feed request/acknowledgment, shooter-ready interlock, occupancy transitions, and fault states.

## Design

Compare metering and transfer concepts; record alternatives in local [cad](cad/README.md) and [prototypes](prototypes/README.md). Integrate via [ball_system](../assemblies/ball_system/README.md).

## Current Status

Architecture scaffold only; no feeder design or timing validated.

## Testing

Plan isolated and integrated transfer tests with synchronized observations and failure logs.

## Known Issues

TBD: handoff geometry, timing, and readiness conditions are undefined.

## Related GitHub Issues

TBD: link actual feeder-interface and test issues when created.
