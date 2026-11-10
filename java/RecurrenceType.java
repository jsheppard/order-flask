package com.sbsolutions.order.models;

/**
 * Enumeration for the type of recurrence pattern for a scheduled order.
 * <p>
 * Defines whether a scheduled order recurs weekly or monthly.
 * </p>
 */
public enum RecurrenceType {
  /** Order recurs on a specific day of the week. */
  WEEKLY,
  /** Order recurs on a specific day of the month (e.g., first Friday). */
  MONTHLY
}
