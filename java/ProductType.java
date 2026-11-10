package com.sbsolutions.order.models;

/**
 * Enumeration of product catalog categories used in pricing configuration.
 * <p>
 * Associates a {@link PricingSheet} entry with a product category to drive
 * display grouping, filtering, and pricing logic.
 * </p>
 *
 * @see PricingSheet
 */
public enum ProductType {

  /** Standard donut products. */
  DONUT,

  /** Donut hole products. */
  DONUT_HOLE,

  /** Roll products (e.g., cinnamon rolls). */
  ROLL,

  /** Mix or bulk product packages. */
  MIX,

  /** Big donut product items. */
  BIG_DONUT,

  /** Beverage products. */
  BEVERAGE,
  
  /** Miscellaneous products that do not fit another category. */
  OTHER
}
