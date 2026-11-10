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
 * Represents a frosting customization option for donuts.
 * <p>
 * Frosting options are selectable at order time when a {@link Donut} has
 * {@code frosting == true}. Includes image URLs for displaying the option in the UI.
 * Equality is based solely on {@code id}.
 * </p>
 *
 * @see Donut#frosting
 * @see Item#frostingId
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Frosting implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** Human-readable frosting description (e.g., "Chocolate", "Vanilla"). */
  String description;

  /** Legacy image URL for backward compatibility. */
  String url;

  /** URL for the full-resolution frosting image. */
  String imageOriginal;

  /** URL for the medium-resolution frosting image. */
  String imageMedium;

  /** URL for the small-resolution frosting image. */
  String imageSmall;

  /** URL for the icon-resolution frosting image. */
  String imageIcon;

}
