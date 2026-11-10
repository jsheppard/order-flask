package com.sbsolutions.order.models;

import java.io.Serial;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;

/**
 * Represents a roll product (e.g., cinnamon roll) in the catalog.
 * <p>
 * This class models a roll item. Extends {@link Product} to inherit all product fields including
 * pricing, availability schedule, and image URLs. Pastry-specific customization options
 * (frosting, icing, topping) are defined by the {@link IsPastry} interface. The roll's item
 * type can be set via the inherited {@code itemType} field using {@link ItemType#ROLL} or other
 * relevant {@link ItemType} values. Equality is based solely on {@code id}.
 * </p>
 *
 * @see Product
 * @see IsPastry
 * @see ItemType
 * @see Donut
 * @see Merchandise
 */
@Data
@SuperBuilder
@EqualsAndHashCode(callSuper = true)
public class Roll extends Product implements IsPastry, AllowDozen {

  @Serial
  private static final long serialVersionUID = 1L;

  public Roll() {}

  /** Whether a frosting customization option is available for this roll. */
  protected boolean frosting;

  /** Whether selecting a frosting is required when ordering this roll. */
  protected boolean requiredFrosting;

  /** Whether an icing customization option is available for this roll. */
  protected boolean icing;

  /** Whether selecting an icing is required when ordering this roll. */
  protected boolean requiredIcing;

  /** Whether a topping customization option is available for this roll. */
  protected boolean topping;

  /** Whether selecting a topping is required when ordering this roll. */
  protected boolean requiredTopping;

  /** Whether this roll can be mixed with other items in the same order. */
  protected boolean allowMix;

  /** Whether this roll can be ordered by the dozen. Never true together with {@link #productDozen}. */
  protected boolean allowDozen = false;

  /**
   * Whether this roll is a single item whose customer can choose a dozen-enabled product instead.
   * Never true together with {@link #allowDozen}.
   */
  protected boolean productDozen = false;

  /**
   * Sets whether this roll can be ordered by the dozen. Setting it to true clears {@link
   * #productDozen}.
   *
   * @param allowDozen true if this roll can be ordered by the dozen
   */
  public void setAllowDozen(boolean allowDozen) {
    this.allowDozen = allowDozen;
    if (allowDozen) {
      this.productDozen = false;
    }
  }

  /**
   * Sets whether this roll is a single item with a dozen option. Setting it to true clears {@link
   * #allowDozen}.
   *
   * @param productDozen true if the customer can choose a dozen-enabled product for this roll
   */
  public void setProductDozen(boolean productDozen) {
    this.productDozen = productDozen;
    if (productDozen) {
      this.allowDozen = false;
    }
  }

}
