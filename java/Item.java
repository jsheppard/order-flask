package com.sbsolutions.order.models;

import java.io.Serial;
import java.io.Serializable;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;

/**
 * Represents a line item within a customer {@link Order}.
 * <p>
 * Captures the product being ordered, its quantity, pricing snapshot, and any
 * customization selections (frosting, icing, topping). Product and pricing details
 * are denormalized at order time so that the order record is self-contained even
 * if catalog data changes later.
 * </p>
 * <p>
 * Equality is based solely on {@code id}.
 * </p>
 *
 * @see Order
 * @see ItemType
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Item implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** The ID of the parent {@link Order} this item belongs to. */
  String orderId;

  /** The catalog ID of the product (e.g., {@link Donut#id} or {@link Roll#id}). */
  String itemId;

  /** The product category for this line item. */
  ItemType itemType;

  /** Quantity ordered. */
  Integer qty;

  // Product information (denormalized snapshot at order time)

  /** Display name of the product at the time of ordering. */
  String productName;

  /** Image URL of the product at the time of ordering. */
  String productImageUrl;

  /** Unit of measure (e.g., {@code "EA"} for each). */
  String productUnit;

  /** Price per unit at the time of ordering. */
  Double unitPrice;

  /** Total price for this line item ({@code unitPrice * qty}). */
  Double lineTotal;

  // Customization details

  /** ID of the selected {@link Frosting} option, or {@code null} if none. */
  String frostingId;

  /** Display name of the selected frosting option, or {@code null} if none. */
  String frostingName;

  /** ID of the selected {@link Icing} option, or {@code null} if none. */
  String icingId;

  /** Display name of the selected icing option, or {@code null} if none. */
  String icingName;

  /** ID of the selected {@link Topping} option, or {@code null} if none. */
  String toppingId;

  /** Display name of the selected topping option, or {@code null} if none. */
  String toppingName;

  /** Free-text notes or special instructions for this line item, or {@code null} if none. */
  String notes;

  /** Whether this item can be mixed with other items in the same order. */
  boolean mix;

  // Dozen details

  /** ID of the dozen grouping this item belongs to, or {@code null} if none. */
  String dozenId;

  /** Display name of the dozen grouping this item belongs to, or {@code null} if none. */
  String dozenName;

  /** ID of the dozen-enabled product the customer chose for this item, or {@code null} if none. */
  String dozenProductId;

  /** Display name of the dozen-enabled product the customer chose, or {@code null} if none. */
  String dozenProductName;

  /** Brand or manufacturer of the merchandise item (if applicable). */
  String brand;

  /** Size of the merchandise item (if applicable). */
  String size;

  /** Color of the merchandise item (if applicable). */
  String color;

  /** Material or fabric composition of the merchandise item (if applicable). */
  String material;
}
