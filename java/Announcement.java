package com.sbsolutions.order.models;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.io.Serial;
import java.io.Serializable;
import java.time.Instant;
import java.time.LocalDate;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;

/**
 * Represents a general announcement or event to be displayed in the calendar view.
 * <p>
 * Stores title, description, date range, and optional color for visual categorization.
 * </p>
 *
 * @see GeneralAnnouncementsView
 */
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Announcement implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** Display title for this announcement. Required; must not be blank. */
  @NotBlank(message = "Title is required and cannot be blank")
  String title;

  /** Detailed description of the announcement. */
  String description;

  /** Start date for this announcement. Required; must not be null. */
  @NotNull(message = "Start date is required")
  LocalDate startDate;

  /** End date for this announcement. If null, treated as a single-day event. */
  LocalDate endDate;

  /** Optional hex color code (e.g., "#FF5733") for visual categorization. Defaults to primary blue. */
  @Builder.Default
  String color = "#2962FF";

  /** Whether this announcement is currently active. Defaults to {@code true}. */
  @Builder.Default
  boolean active = true;

  /** Timestamp of creation. */
  Instant createdAt;

  /** User who created this announcement. */
  String createdBy;

  /**
   * Returns the actual end date for this announcement.
   * If {@code endDate} is null, returns {@code startDate}.
   *
   * @return the end date, or start date if end date is not set
   */
  public LocalDate getEffectiveEndDate() {
    return endDate != null ? endDate : startDate;
  }

  /**
   * Returns whether this announcement spans multiple days.
   *
   * @return {@code true} if end date is set and differs from start date
   */
  public boolean isMultiDay() {
    return endDate != null && !endDate.equals(startDate);
  }
}
