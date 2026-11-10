package com.sbsolutions.order.models;

/**
 * Enumeration representing the operational ordering status of the store.
 * <p>
 * Controls whether customers can place new orders and is associated with
 * configurable time windows via {@link Status}.
 * </p>
 *
 * @see Status
 */
public enum OrderPlacementStatus {

  /** Ordering is disabled and unavailable to customers. */
  OFF,

  /** Ordering is scheduled but not yet open. */
  SCHEDULED,

  /** Ordering is currently open and accepting orders. */
  OPEN,

  /** Ordering window has closed; no new orders are accepted. */
  CLOSED
}
