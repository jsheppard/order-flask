package com.sbsolutions.order.models;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalTime;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;

/**
 * Represents the order placement status configuration for the store.
 * <p>
 * Controls when customers can place orders by defining an operational status
 * ({@link OrderPlacementStatus}) along with an optional time window and the
 * customer-facing messages displayed for each order outcome.
 * Equality is based solely on {@code id}.
 * </p>
 *
 * @see OrderPlacementStatus
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Status implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** The current operational ordering status. */
  OrderPlacementStatus status;

  /** The time of day when the ordering window opens. */
  LocalTime startTime;

  /** The time of day when the ordering window closes. */
  LocalTime endTime;

  /** Message displayed to the customer when their order is pending review. */
  String pendingMessage;

  /** Subject line for the pending order notification. */
  @Builder.Default
  String pendingSubject = "Order Pending";

  /** Message displayed to the customer when their order is approved. */
  String approvedMessage;

  /** Subject line for the approved order notification. */
  @Builder.Default
  String approvedSubject = "Order Approved";

  /** Message displayed to the customer when their order is declined. */
  String declinedMessage;

  /** Subject line for the declined order notification. */
  @Builder.Default
  String declinedSubject = "Order Declined";

  /** Message displayed to the customer when their order is completed. */
  String completedMessage;

  /** Subject line for the completed order notification. */
  @Builder.Default
  String completedSubject = "Order Completed";

  /** Message displayed to the customer when their order is denied. */
  String deniedMessage;

  /** Subject line for the denied order notification. */
  @Builder.Default
  String deniedSubject = "Order Denied";

  /** Message displayed to the customer when their order has been deleted. */
  String deletedMessage;

  /** Subject line for the deleted order notification. */
  @Builder.Default
  String deletedSubject = "Order Deleted";

  /** Message displayed to staff members. */
  String staffMessage;

  /** Announcement displayed on the public home page. Blank or null hides it. */
  String announcement;
}
