package com.sbsolutions.order.models;

import java.io.Serial;
import java.io.Serializable;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;

/**
 * Represents a capacity limit for a single {@link ItemType}.
 * <p>
 * Pairs an item type with an integer capacity value indicating the maximum
 * number of that type allowed, and an optional sheet size indicating how many
 * items fit on a single baking sheet. Use {@link #createDefaults()} to obtain
 * a list pre-populated with every {@link ItemType} at a capacity of {@code -1}
 * (unconstrained) and a {@code null} sheet size.
 * </p>
 *
 * @see ItemType
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ItemTypeLimit implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** The unique identifier for this limit. */
  @Id
  String id;

  /** The item type this limit applies to. */
  ItemType itemType;

  /** The maximum capacity allowed for this item type. */
  Integer capacity;

  /** The number of items that fit on a single baking sheet for this type. May be {@code null} if not configured. */
  Integer sheetSize;

  /**
   * Creates a list of {@link ItemTypeLimit} entries — one per {@link ItemType} —
   * each initialized with a {@code capacity} of {@code -1} (unconstrained) and
   * a {@code null} sheet size.
   *
   * @return a list containing an entry for every {@link ItemType} with capacity {@code -1}
   */
  public static List<ItemTypeLimit> createDefaults() {
    return Arrays.stream(ItemType.values())
        .map(type -> new ItemTypeLimit(null, type, -1, null))
        .collect(Collectors.toList());
  }
}
