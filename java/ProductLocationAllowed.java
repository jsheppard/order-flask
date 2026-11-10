package com.sbsolutions.order.models;

/**
 * Enumeration of allowed delivery/pickup locations for a product.
 * <p>
 * Specifies whether a product is available for pickup, delivery, or both.
 * </p>
 */
public enum ProductLocationAllowed {

  /** Product is available for both pickup and delivery. */
  ANY,

  /** Product is available for pickup only. */
  PICKUP,

  /** Product is available for delivery only. */
  DELIVERY
}
