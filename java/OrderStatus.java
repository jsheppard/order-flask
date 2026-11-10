package com.sbsolutions.order.models;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * Enumeration of possible order statuses.
 */
@Getter
@RequiredArgsConstructor
public enum OrderStatus {

  /** The order has been submitted and is waiting for staff review and approval. */
  PENDING("Pending"),

  /** The order has been reviewed and approved by staff and is ready for production. */
  APPROVED("Approved"),

  /** The order has been prepared, fulfilled, and picked up or delivered. */
  COMPLETED("Completed"),

  /** The order has been reviewed and explicitly denied by staff (e.g., unavailable capacity). */
  DENIED("Denied"),

  /** The order was not processed, typically due to payment failure or technical reasons. */
  DECLINED("Declined"),

  /** The order has been logically deleted from the system and should not be displayed in active views. */
  DELETED("Deleted");

  private final String label;

  @Override
  public String toString() {
    return label;
  }

  /**
   * Returns the OrderStatus matching the given label, case-insensitive.
   *
   * @param label the label to match
   * @return the matching OrderStatus, or PENDING if no match is found
   */
  public static OrderStatus fromLabel(String label) {
    if (label == null) return PENDING;
    for (OrderStatus status : values()) {
      if (status.label.equalsIgnoreCase(label) || status.name().equalsIgnoreCase(label)) {
        return status;
      }
    }
    return PENDING;
  }
}
