package com.sbsolutions.order.models;

import java.io.Serial;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;

/**
 * Represents a merchandise product in the catalog.
 * <p>
 * This class models a merchandise item for non-bakery products such as cups, shirts, and other
 * branded items. All product data including pricing, availability schedule, and image URLs are
 * inherited from {@link Product}. Merchandise-specific attributes such as size, color, material,
 * and brand are defined in this class. Equality is based solely on {@code id}.
 * </p>
 *
 * @see Product
 * @see HasImageUrls
 * @see ItemType
 * @see Donut
 * @see Roll
 */
@Data
@SuperBuilder
@EqualsAndHashCode(callSuper = true)
public class Merchandise extends Product {

  @Serial
  private static final long serialVersionUID = 1L;

  public Merchandise() {}

  /** Size of the merchandise item (e.g., "S", "M", "L", "XL"). */
  protected String size;

  /** Color of the merchandise item. */
  protected String color;

  /** Material or fabric composition of the merchandise item. */
  protected String material;

  /** Brand or manufacturer of the merchandise item. */
  protected String brand;

  /** Whether this merchandise item is available in multiple sizes. */
  protected boolean hasSizeOptions;

  /** Whether this merchandise item is available in multiple colors. */
  protected boolean hasColorOptions;

}
