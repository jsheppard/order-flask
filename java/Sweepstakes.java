package com.sbsolutions.order.models;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalDate;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;

import jakarta.validation.constraints.NotNull;

/**
 * Represents a sweepstakes contest in the Randy's ordering system.
 * <p>
 * This class models a sweepstakes campaign, capturing contest details, dates,
 * prize information, and the list of entered participants. Sweepstakes are
 * persisted to MongoDB and identified by a unique string ID.
 * </p>
 * <p>
 * Required fields: {@code title}, {@code description}, {@code beginDate}, and {@code endDate}.
 * These fields must be set and cannot be {@code null}.
 * </p>
 * <p>
 * Equality is based solely on {@code id}, so two {@code Sweepstakes} objects
 * with the same ID are considered equal regardless of other field values.
 * </p>
 */
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Sweepstakes implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** Title of the sweepstakes. */
  @NotNull
  String title;

  /** Description of the sweepstakes. */
  @NotNull
  String description;

  /** The date when the sweepstakes begins. */
  @NotNull
  LocalDate beginDate;

  /** The date when the sweepstakes ends. */
  @NotNull
  LocalDate endDate;

  /** URL of the sweepstakes image. */
  String imageUrl;

  /** Email address of the sweepstakes winner, or {@code null} if not yet selected. */
  String winnerEmail;

  /** The date the winner was selected, or {@code null} if not yet determined. */
  LocalDate winnerDate;

  /** Unique ticket number for the winner, generated when a winner is selected. */
  String ticketNumber;

  /** List of user IDs or customer IDs that have entered the sweepstakes. */
  List<String> enteredUsers;

  /** Google Calendar event ID for this sweepstakes, or {@code null} if not yet created. */
  String calendarEventId;

  /** The timestamp when this sweepstakes was created. */
  @CreatedDate
  java.time.Instant createdAt;

  /** The timestamp when this sweepstakes was last updated. */
  @LastModifiedDate
  java.time.Instant updatedAt;
}
