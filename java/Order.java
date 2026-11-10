package com.sbsolutions.order.models;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalDate;
import java.util.Date;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;

/**
 * Represents a customer order in the Randy's ordering system.
 * <p>
 * This class models a complete order, capturing customer contact information,
 * scheduling details, fulfillment type, and the list of ordered items. Orders
 * are persisted to MongoDB and identified by a unique string ID.
 * </p>
 * <p>
 * Equality is based solely on {@code id}, so two {@code Order} objects with the
 * same ID are considered equal regardless of other field values.
 * </p>
 *
 * @see Item
 * @see OrderType
 * @see OrderStatus
 */
@Data
@SuperBuilder
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Order implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** The username or identifier of the user who created this order. */
  String createdBy;

  /** The internal customer ID associated with this order. */
  Integer customerId;

  /** The customer's display name for the order. */
  String name;

  /** The customer's email address for order notifications. */
  String email;

  /** The customer's phone number for order contact. */
  String phone;

  /** The date and time the order was placed. */
  Date orderDate;

  /** The fulfillment type (delivery or pickup). Defaults to {@link OrderType#DELIVERY}. */
  @Builder.Default
  OrderType type = OrderType.DELIVERY;

  /** The requested delivery or pickup date. */
  LocalDate deliverDate;

  /** Whether the order has been approved by staff. */
  boolean approved;

  /** The date the order was approved. */
  LocalDate approvedDate;

  /** The ID of the location associated with this order. */
  String locationId;

  /** The current status for the order. Defaults to {@link OrderStatus#PENDING}. */
  @Builder.Default
  OrderStatus status = OrderStatus.PENDING;

  /** The Google Calendar event ID linked to this order's scheduled date. */
  String calendarEventId;

  /** The list of items included in this order. */
  List<Item> items;

  /** Optional free-text notes or special instructions from the customer. */
  String notes;

  /** The timestamp when this order was created. */
  @CreatedDate
  java.time.Instant createdAt;

  /** The timestamp when this order was last updated. */
  @LastModifiedDate
  java.time.Instant updatedAt;

  /** Slack channel ID holding this order's notification while it is pending, or {@code null}. */
  String slackChannelId;

  /** Slack timestamp of this order's pending notification, used to update or delete it. */
  String slackMessageTs;
}
