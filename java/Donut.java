package com.sbsolutions.order.models;

import java.io.Serial;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;

/**
 * Represents a donut product in the catalog.
 * <p>
 * This class models a donut item. All product data including pricing, availability schedule,
 * and image URLs are inherited from {@link Product}. Pastry-specific customization options
 * (frosting, icing, topping) are defined by the {@link IsPastry} interface. The donut's item
 * type can be set via the inherited {@code itemType} field using one of the donut-specific
 * {@link ItemType} values (e.g., {@link ItemType#GLAZED_DONUT}, {@link ItemType#CAKE_DONUT},
 * etc.). Equality is based solely on {@code id}.
 * </p>
 *
 * @see Product
 * @see IsPastry
 * @see ItemType
 * @see Roll
 * @see Merchandise
 */
@Data
@SuperBuilder
@EqualsAndHashCode(callSuper = true)
public class Donut extends Product implements IsPastry, AllowDozen {

  @Serial
  private static final long serialVersionUID = 1L;

  public Donut() {}

  /** Whether a frosting customization option is available for this donut. */
  protected boolean frosting;

  /** Whether selecting a frosting is required when ordering this donut. */
  protected boolean requiredFrosting;

  /** Whether an icing customization option is available for this donut. */
  protected boolean icing;

  /** Whether selecting an icing is required when ordering this donut. */
  protected boolean requiredIcing;

  /** Whether a topping customization option is available for this donut. */
  protected boolean topping;

  /** Whether selecting a topping is required when ordering this donut. */
  protected boolean requiredTopping;

  /** Whether this donut can be mixed with other items in the same order. */
  protected boolean allowMix;

  /** Whether this donut can be ordered by the dozen. Never true together with {@link #productDozen}. */
  protected boolean allowDozen = false;

  /**
   * Whether this donut is a single item whose customer can choose a dozen-enabled product instead.
   * Never true together with {@link #allowDozen}.
   */
  protected boolean productDozen = false;

  /**
   * Sets whether this donut can be ordered by the dozen. Setting it to true clears {@link
   * #productDozen}.
   *
   * @param allowDozen true if this donut can be ordered by the dozen
   */
  public void setAllowDozen(boolean allowDozen) {
    this.allowDozen = allowDozen;
    if (allowDozen) {
      this.productDozen = false;
    }
  }

  /**
   * Sets whether this donut is a single item with a dozen option. Setting it to true clears {@link
   * #allowDozen}.
   *
   * @param productDozen true if the customer can choose a dozen-enabled product for this donut
   */
  public void setProductDozen(boolean productDozen) {
    this.productDozen = productDozen;
    if (productDozen) {
      this.allowDozen = false;
    }
  }

}
