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
 * Represents an icing customization option for donuts.
 * <p>
 * Icing options are selectable at order time when a {@link Donut} has
 * {@code icing == true}. Equality is based solely on {@code id}.
 * </p>
 *
 * @see Donut#icing
 * @see Item#icingId
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Icing implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** Human-readable icing description (e.g., "Chocolate", "Vanilla"). */
  String description;

  /** Image URL for displaying this icing option. */
  String url;

}
