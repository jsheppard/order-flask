package com.sbsolutions.order.models;

import java.time.DayOfWeek;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

/**
 * Represents a scheduled recurring order in the Randy's ordering system.
 * <p>
 * Extends {@link Order} to add support for scheduled recurring orders, supporting both:
 * <ul>
 *   <li><b>Weekly recurrence</b>: order recurs on a specific day of the week (e.g., every Friday)
 *   <li><b>Monthly recurrence</b>: order recurs on a specific pattern day of the month (e.g., first Friday)
 * </ul>
 * </p>
 *
 * @see Order
 * @see RecurrenceType
 * @see MonthlyDayPattern
 */
@Getter
@Setter
@ToString(callSuper = true)
@SuperBuilder
@AllArgsConstructor
@NoArgsConstructor
public class ScheduledOrder extends Order {

  /** The day of the week (1-7, where 1=Monday and 7=Sunday). Used for weekly recurrence. */
  Integer weekDay;

  /** The type of recurrence pattern (weekly or monthly). Defaults to WEEKLY for backward compatibility. */
  @Builder.Default
  RecurrenceType recurrenceType = RecurrenceType.WEEKLY;

  /** The specific pattern for monthly recurrence (first, second, third, etc.). Only used when recurrenceType is MONTHLY. */
  MonthlyDayPattern monthlyPattern;

  /** The day of the week for monthly recurrence (Monday, Tuesday, etc.). Only used when recurrenceType is MONTHLY. */
  DayOfWeek monthlyDayOfWeek;
}
