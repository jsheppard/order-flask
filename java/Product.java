package com.sbsolutions.order.models;

import jakarta.validation.constraints.NotBlank;
import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;
import org.springframework.data.annotation.Id;

/**
 * Base class for product items in the catalog.
 * <p>
 * This class encapsulates common product data including pricing, customization options,
 * availability schedule, and image URLs. It implements {@link HasImageUrls} to support
 * multiple image size variants. Subclasses include {@link Donut}, {@link Roll}, and
 * {@link Merchandise}. Equality is based solely on {@code id}.
 * </p>
 *
 * @see Donut
 * @see Roll
 * @see Merchandise
 * @see HasImageUrls
 * @see ItemType
 */
@Data
@SuperBuilder
@AllArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Product implements Serializable, HasImageUrls {

  @Serial
  private static final long serialVersionUID = 1L;

  public Product() {}

  /** MongoDB document ID. */
  @Id
  protected String id;

  /** Display sort order for catalog listings. Defaults to {@code 0}. */
  @Builder.Default
  protected Integer order = 0;

  /** Human-readable product description. Required; must not be blank. */
  @NotBlank
  protected String description;

  /** Regular price of this product. Required. */
  @NotBlank
  protected BigDecimal price;

  /** Optional promotional price, active during {@link #specialPriceDate}. */
  protected BigDecimal specialPrice;

  /** The date on which {@link #specialPrice} is active. */
  protected Date specialPriceDate;

  /** Item type classification for this product (e.g., {@link ItemType#GLAZED_DONUT}). */
  protected ItemType itemType;

  /** Allowed location types for this product (pickup, delivery, or both). Defaults to {@code ANY}. */
  @Builder.Default
  protected ProductLocationAllowed locationAllowed = ProductLocationAllowed.ANY;

  /** Unit of measure (e.g., {@code "EA"} for each). */
  protected String unit;

  /** Legacy image URL for backward compatibility. */
  protected String url;

  /** Comma-separated or encoded string of days this product is available. */
  protected String availableDays;

  /** URL for the full-resolution product image. */
  protected String imageOriginal;

  /** URL for the medium-resolution product image. */
  protected String imageMedium;

  /** URL for the small-resolution product image. */
  protected String imageSmall;

  /** URL for the icon-resolution product image. */
  protected String imageIcon;

  /** URL for the thumbnail product image. */
  protected String imageThumbnail;

}
