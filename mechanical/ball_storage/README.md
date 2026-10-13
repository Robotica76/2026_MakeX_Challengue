# Ball Storage

## Purpose

Investigate retaining and organizing balls between acquisition and feeding.

## Competition Capabilities

Candidate: controlled ball retention. Permitted possession and handling constraints require official verification.

## Requirements

TBD: sourced capacity constraints, retention conditions, occupancy observability, and service needs.

## Mechanical Interfaces

TBD: [intake](../ball_intake/README.md) entry, [feeder](../feeder/README.md) exit, and chassis mounts.

## Electrical Interfaces

TBD: occupancy sensing and any actuation, routing, and power needs with [electrical](../../electrical/README.md).

## Software Interfaces

TBD: occupancy representation, transfer requests, full/empty semantics, and recovery interlocks.

## Design

Compare passive and active organization concepts without assuming either. Keep local models in [cad](cad/README.md); reference them through [ball_system](../assemblies/ball_system/README.md).

## Current Status

Architecture scaffold only; no capacity or mechanism selected.

## Testing

Plan retention, occupancy-estimation, and handoff trials after defining sourced constraints.

## Known Issues

TBD: capacity, element properties, and transfer coordination remain unresolved.

## Related GitHub Issues

TBD: link actual storage requirements and validation issues when created.
