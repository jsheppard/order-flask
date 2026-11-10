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
 * Represents a topping customization option for donuts.
 * <p>
 * Topping options are selectable at order time when a {@link Donut} has
 * {@code topping == true}. Equality is based solely on {@code id}.
 * </p>
 *
 * @see Donut#topping
 * @see Item#toppingId
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Topping implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** Human-readable topping description (e.g., "Sprinkles", "Chocolate Chips"). */
  String description;

  /** Image URL for displaying this topping option. */
  String url;

}
