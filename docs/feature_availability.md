# Feature Availability Policy

## Prediction Point

The system generates a disruption-risk score 6 hours before the scheduled departure time.

A feature may be used only when it would reasonably be available at that prediction point.

## Prediction-Safe Features

The initial model may use:

- Flight date
- Month
- Day of week
- Scheduled departure time
- Scheduled arrival time
- Scheduled elapsed time
- Reporting airline
- Flight number
- Origin airport
- Destination airport
- Route
- Flight distance
- Holiday indicators
- Historical airline disruption rates
- Historical airport disruption rates
- Historical route disruption rates
- Weather forecasts available at the prediction point

Historical aggregate features must be calculated using only flights occurring before the flight being scored.

## Label-Only Columns

These columns may be used to construct or evaluate the target but must never be provided to the model:

- Arrival delay
- Cancellation indicator
- Cancellation code
- Diversion indicator

## Prohibited Post-Departure Features

The model must not use:

- Actual departure time
- Departure delay
- Taxi-out time
- Wheels-off time
- Wheels-on time
- Taxi-in time
- Actual arrival time
- Actual elapsed time
- Air time
- Carrier-delay minutes
- Weather-delay minutes
- National Air System delay minutes
- Security-delay minutes
- Late-aircraft-delay minutes

These values describe outcomes or events occurring after the prediction point and would cause target leakage.

## Conditionally Available Features

The following features will be excluded from the initial model until their availability 6 hours before departure can be demonstrated:

- Tail number
- Assigned aircraft
- Incoming-aircraft status
- Crew status
- Gate assignment

## Validation Rule

Every model feature must have a documented source, calculation method, and availability time. Features with uncertain availability will be excluded by default.
