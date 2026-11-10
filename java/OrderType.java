package com.sbsolutions.order.models;

/**
 * Enumeration of order fulfillment types.
 * <p>
 * Specifies how a customer's order will be fulfilled. The default type on {@link Order}
 * is {@link #DELIVERY}.
 * </p>
 *
 * @see Order
 */
public enum OrderType {

  /** Customer will pick up the order at the store location. */
  PICKUP,

  /** Order will be delivered to the customer's address. */
  DELIVERY,

  /** Standard order with no specific fulfillment preference. */
  STANDARD
}
