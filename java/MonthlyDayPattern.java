package com.sbsolutions.order.models;

/**
 * Enumeration for the specific pattern of a monthly recurring order.
 * <p>
 * Defines which occurrence of a day in the month the order should recur on
 * (e.g., first Friday, second Tuesday, last business day).
 * </p>
 */
public enum MonthlyDayPattern {
  /** First occurrence of the specified day in the month. */
  FIRST_OCCURRENCE(1, "First"),
  /** Second occurrence of the specified day in the month. */
  SECOND_OCCURRENCE(2, "Second"),
  /** Third occurrence of the specified day in the month. */
  THIRD_OCCURRENCE(3, "Third"),
  /** Fourth occurrence of the specified day in the month. */
  FOURTH_OCCURRENCE(4, "Fourth"),
  /** Last occurrence of the specified day in the month. */
  LAST_OCCURRENCE(5, "Last"),
  /** Last business day (Monday-Friday) of the month. */
  LAST_BUSINESS_DAY(6, "Last Business Day");

  private final int occurrenceNumber;
  private final String displayName;

  MonthlyDayPattern(int occurrenceNumber, String displayName) {
    this.occurrenceNumber = occurrenceNumber;
    this.displayName = displayName;
  }

  public int getOccurrenceNumber() {
    return occurrenceNumber;
  }

  public String getDisplayName() {
    return displayName;
  }
}
