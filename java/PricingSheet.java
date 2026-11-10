package com.sbsolutions.order.models;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;

/**
 * Represents a pricing configuration entry for a product at a specific location.
 * <p>
 * Each {@code PricingSheet} row defines a product's price, type, and display order
 * for a given store location. Multiple entries per location allow location-specific
 * pricing. Equality is based solely on {@code id}.
 * </p>
 *
 * @see ProductType
 * @see Location
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class PricingSheet implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** The ID of the {@link Location} this pricing entry applies to. */
  String locationId;

  /** Display sort order for this entry within the pricing sheet. */
  Integer order;

  /** The product category for this pricing entry. */
  ProductType productType;

  /** Short product code used for identification (e.g., {@code "GLZD"}). */
  String productCode;

  /** Human-readable product description (e.g., "Glazed Donut"). */
  String description;

  /** Unit of measure (e.g., {@code "EA"} for each, {@code "DOZ"} for dozen). */
  String unit;

  /** Price for the product at this location. */
  BigDecimal price;

}
