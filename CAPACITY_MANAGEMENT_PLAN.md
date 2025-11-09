# Capacity Management System Plan

## Overview
Build an intelligent capacity management system that alerts management when more TSE's need to be added to the queue based on real-time load, capacity utilization, and projected demand.

## Key Constraints
- **Max Capacity per TSE**: 5 concurrent open chats (snoozed chats don't count toward this limit)
- **Snoozed Overflow**: Snoozed chats can return and add to the load (e.g., 5 open + 5 snoozed returning = 10 total)
- **Availability**: Only TSE's who are "not away" can take new chats

## Available Intercom API Metrics

### Current Metrics We Have:
1. **Conversation State**: `state` (open/snoozed), `snoozed_until` timestamp
2. **Assignment**: `admin_assignee_id`, `team_assignee_id`
3. **Statistics**:
   - `statistics.first_admin_reply_at` - First response time
   - `statistics.time_to_admin_reply` - Response time metrics
   - `statistics.median_time_to_reply` - Median response time
   - `statistics.handling_time` - Time to resolve conversation
   - `statistics.count_conversation_parts` - Activity level
   - `statistics.last_admin_reply_at` - Last activity timestamp
4. **Timestamps**: `created_at`, `updated_at`, `waiting_since`
5. **TSE Status**: `away_mode_enabled` from admin API

### Metrics We Need to Calculate:

#### 1. **Current Capacity Utilization**
- **Per TSE**: `(open_chats / 5) * 100%`
- **Team Total**: `sum(open_chats_per_available_tse) / (available_tse_count * 5)`
- **At-Capacity TSE's**: Count of TSE's with `open_chats >= 5`

#### 2. **Snoozed Return Projection**
- **Returning Soon**: Count snoozed chats where `snoozed_until <= now + 1 hour`
- **Returning in 2 Hours**: Count where `snoozed_until <= now + 2 hours`
- **Returning Today**: Count where `snoozed_until` is today
- **Projected Load**: `current_open + snoozed_returning_soon`

#### 3. **Response Velocity Metrics**
- **Conversations Handled per Hour**: Track closed conversations per TSE per hour
- **Average Response Time Trend**: Compare current hour vs previous hour
- **Active TSE Count**: TSE's who replied to a conversation in last 30 minutes

#### 4. **Queue Depth & Pressure**
- **Unassigned Queue**: Count of unassigned open conversations
- **Waiting Queue**: Count waiting for first reply
- **Queue Growth Rate**: Change in queue size over last 15 minutes

## Capacity Alert System

### Alert Levels

#### 🟢 **GREEN (Optimal)**
- **Conditions**:
  - Available capacity > 20% (i.e., < 80% utilization)
  - Unassigned queue < 3
  - Average wait time < SLA threshold
- **Action**: No action needed

#### 🟡 **YELLOW (Warning)**
- **Conditions** (any of):
  - Available capacity 10-20%
  - Unassigned queue 3-7
  - Average wait time approaching SLA (80-100% of threshold)
  - 2+ TSE's at capacity (5/5 chats)
- **Action**: Monitor closely, prepare to add TSE's

#### 🟠 **ORANGE (Caution)**
- **Conditions** (any of):
  - Available capacity 5-10%
  - Unassigned queue 8-12
  - Average wait time > SLA threshold
  - 3+ TSE's at capacity
  - Snoozed returns projected to exceed capacity in next hour
- **Action**: Consider adding 1-2 TSE's

#### 🔴 **RED (Critical)**
- **Conditions** (any of):
  - Available capacity < 5%
  - Unassigned queue > 12
  - Average wait time > 2x SLA threshold
  - 50%+ of available TSE's at capacity
  - Projected overload in next 30 minutes
- **Action**: **Immediately add TSE's** (calculate exact number needed)

### Capacity Calculation Formula

```
Available TSE's = Total TSE's - Away TSE's
Current Capacity = Available TSE's × 5
Current Load = Sum of open chats per available TSE
Available Capacity = Current Capacity - Current Load
Utilization % = (Current Load / Current Capacity) × 100

Projected Load = Current Load + Snoozed Returning in Next Hour
Projected Capacity Needed = Projected Load / 5
Additional TSE's Needed = max(0, ceil(Projected Capacity Needed) - Available TSE's)
```

## Dashboard Widget Design

### New Widget: "Capacity Status"

**Location**: Top row, between "Waiting 1st Reply" and "Open vs Snoozed"

**Display Elements**:

1. **Status Indicator** (Large, color-coded)
   - Green/Yellow/Orange/Red circle or badge
   - Current status text: "Optimal" / "Warning" / "Caution" / "Critical"

2. **Key Metrics** (Grid layout)
   - **Available Capacity**: "X / Y chats" (e.g., "12 / 25 chats")
   - **Utilization**: "XX%" with color coding
   - **At Capacity TSE's**: "X TSE's at max"
   - **Snoozed Returning**: "X returning in 1h"

3. **Recommendation Box** (Conditional)
   - **When action needed**: "Add X TSE's to queue"
   - **When optimal**: "No action needed"
   - **When warning**: "Monitor - may need X TSE's soon"

4. **Mini Chart** (Below metrics)
   - Line graph showing capacity utilization over last 2 hours
   - X-axis: Time increments
   - Y-axis: Utilization percentage
   - Color-coded zones (green/yellow/orange/red thresholds)

### Enhanced TSE Table

Add columns to existing TSE table:
- **Capacity**: "X / 5" (e.g., "3 / 5")
- **Utilization Bar**: Visual progress bar showing capacity
- **Snoozed**: Count of snoozed chats (for overflow awareness)
- **Status**: "Available" / "At Capacity" / "Away"

## Implementation Steps

### Phase 1: Data Collection
1. ✅ Already have: Open/snoozed counts per TSE
2. **Add**: Fetch `snoozed_until` timestamps for all snoozed conversations
3. **Add**: Track `statistics.last_admin_reply_at` to identify active TSE's
4. **Add**: Calculate response velocity (conversations handled per hour)

### Phase 2: Capacity Calculations
1. **Create**: `intercom_dashboard/capacity.py` module
   - `calculate_capacity_metrics()` function
   - `project_snoozed_returns()` function
   - `calculate_tse_utilization()` function
   - `determine_alert_level()` function

### Phase 3: API Endpoint
1. **Add**: `/api/capacity` endpoint in `app/main.py`
   - Returns capacity metrics, alert level, recommendations
   - Includes snoozed return projections

### Phase 4: UI Components
1. **Create**: Capacity Status widget in `templates/index.html`
2. **Add**: Capacity columns to TSE table
3. **Add**: Capacity utilization chart
4. **Style**: Color-coded alerts matching dashboard theme

### Phase 5: Historical Tracking (Future Enhancement)
1. Store capacity metrics over time
2. Identify patterns (peak hours, days)
3. Predictive alerts based on historical trends

## API Endpoint Structure

```python
GET /api/capacity?team_id=5480079

Response:
{
  "alert_level": "orange",  # green/yellow/orange/red
  "status": "Caution",
  "current_capacity": {
    "available_tse_count": 5,
    "total_capacity": 25,  # available_tse_count * 5
    "current_load": 18,
    "available_capacity": 7,
    "utilization_percent": 72.0,
    "at_capacity_tse_count": 2
  },
  "snoozed_projection": {
    "returning_in_1h": 3,
    "returning_in_2h": 7,
    "returning_today": 12
  },
  "projected_load": {
    "in_1h": 21,  # current_load + returning_in_1h
    "in_2h": 25,
    "capacity_needed_in_1h": 5,  # ceil(21/5)
    "capacity_needed_in_2h": 5   # ceil(25/5)
  },
  "recommendation": {
    "action": "add_tse",
    "count": 1,
    "reason": "Projected load will exceed capacity in 1 hour",
    "urgency": "medium"  # low/medium/high/critical
  },
  "tse_details": [
    {
      "admin_id": "123",
      "name": "John Doe",
      "open_chats": 5,
      "snoozed_chats": 3,
      "utilization_percent": 100.0,
      "status": "at_capacity",
      "away": false
    },
    ...
  ],
  "queue_metrics": {
    "unassigned": 5,
    "waiting_first_reply": 8,
    "queue_growth_rate": 0.5  # conversations per minute
  }
}
```

## Configuration

Add to `intercom_dashboard/config.py`:
```python
# Capacity management config
MAX_CHATS_PER_TSE = int(os.getenv("MAX_CHATS_PER_TSE", "5"))
CAPACITY_WARNING_THRESHOLD = float(os.getenv("CAPACITY_WARNING_THRESHOLD", "0.8"))  # 80%
CAPACITY_CAUTION_THRESHOLD = float(os.getenv("CAPACITY_CAUTION_THRESHOLD", "0.9"))  # 90%
CAPACITY_CRITICAL_THRESHOLD = float(os.getenv("CAPACITY_CRITICAL_THRESHOLD", "0.95"))  # 95%
SNOOZED_PROJECTION_HOURS = int(os.getenv("SNOOZED_PROJECTION_HOURS", "2"))  # Project 2 hours ahead
```

## Benefits

1. **Proactive Management**: Alerts before capacity is exceeded
2. **Data-Driven Decisions**: Clear metrics on when/how many TSE's to add
3. **Snoozed Awareness**: Accounts for returning snoozed chats
4. **Visual Clarity**: Color-coded alerts for quick status assessment
5. **Historical Insights**: Track capacity trends over time

## Next Steps

1. Review and approve this plan
2. Implement Phase 1 (data collection)
3. Implement Phase 2 (calculations)
4. Implement Phase 3 (API endpoint)
5. Implement Phase 4 (UI components)
6. Test with real data
7. Iterate based on feedback

