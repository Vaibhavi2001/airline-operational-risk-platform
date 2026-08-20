# Project Charter

## Project Name

Airline Operational Risk Intelligence Platform

## Business Stakeholder

Airline Operations Control Center responsible for coordinating flights, aircraft, crews, gates, and disruption response.

## Business Problem

Flight delays and cancellations create operational costs, missed passenger connections, staffing pressure, aircraft scheduling problems, and poor customer experiences.

Operations teams have limited capacity and cannot manually investigate every scheduled flight. They need an early-warning system that identifies which flights require the most attention.

## Project Objective

Develop a machine learning system that assigns each scheduled U.S. domestic flight a probability of experiencing a major operational disruption.

The predictions will help operations teams prioritize flights for preventive review and intervention.

## Prediction Unit

One scheduled U.S. domestic flight.

## Prediction Timing

A risk score will be generated 6 hours before the scheduled departure time.

Only information reasonably available at that prediction point will be used as model input.

## Target Definition

A flight will be labeled as a major disruption when either:

- The flight is cancelled, or
- Its arrival delay is at least 60 minutes.

```text
major_disruption = cancelled OR arrival_delay_minutes >= 60

