package com.sbsolutions.order.models;

/**
 * Enumeration of order line item product classifications.
 * <p>
 * Used on {@link Item}, {@link Donut}, {@link Roll}, and {@link Merchandise} to identify the
 * category of product being ordered or cataloged. The enumeration covers multiple product
 * categories:
 * </p>
 * <p>
 * <strong>Donut Products:</strong> {@link #GLAZED_DONUT}, {@link #GLAZED_DONUT_HOLES},
 * {@link #CAKE_DONUT}, {@link #CAKE_DONUT_HOLES}, {@link #RAISED_DONUT},
 * {@link #RAISED_DONUT_HOLES}, {@link #BIG_DONUT}
 * </p>
 * <p>
 * <strong>Pastry Products:</strong> {@link #ROLL}, {@link #MUFFIN}, {@link #PASTRY},
 * {@link #COOKIE}, {@link #CROISSANT}, {@link #BAGEL}
 * </p>
 * <p>
 * <strong>Beverage & Merchandise:</strong> {@link #BEVERAGE}, {@link #CUP}, {@link #SHIRT}
 * </p>
 * <p>
 * <strong>Dietary & Special Items:</strong> {@link #GLUTEN_FREE}, {@link #VEGAN}, {@link #HALAL}
 * </p>
 * <p>
 * <strong>Other:</strong> {@link #MISC} for miscellaneous items, {@link #MIX} for mixed or bulk
 * assortments
 * </p>
 *
 * @see Item
 * @see Donut
 * @see Roll
 * @see Merchandise
 */
public enum ItemType {

  /** Glazed donut product items. */
  GLAZED_DONUT,

  /** Glazed donut hole product items. */
  GLAZED_DONUT_HOLES,

  /** Cake donut product items. */
  CAKE_DONUT,

  /** Cake donut hole product items. */
  CAKE_DONUT_HOLES,

  /** Raised donut product items. */
  RAISED_DONUT,

  /** Raised donut hole product items. */
  RAISED_DONUT_HOLES,

  /** Roll (e.g., cinnamon roll) product items. */
  ROLL,

  /** Big donut product items. */
  BIG_DONUT,

  /** Muffin product items. */
  MUFFIN,

  /** Pastry product items. */
  PASTRY,

  /** Cookie product items. */
  COOKIE,

  /** Croissant product items. */
  CROISSANT,

  /** Bagel product items. */
  BAGEL,

  /** Beverage product items. */
  BEVERAGE,

  /** Gluten Free product items. */
  GLUTEN_FREE,

  /** Vegan product items. */
  VEGAN,

  /** Halal product items. */
  HALAL,

  /** Cup product items (e.g., coffee cups, branded cups). */
  CUP,

  /** Shirt or apparel product items. */
  SHIRT,

  /** Miscellaneous or other product items. */
  MISC,

  /** Mixed or bulk assortment product items. */
  MIX

}
