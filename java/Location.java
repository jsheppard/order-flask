package com.sbsolutions.order.models;

import jakarta.validation.constraints.NotBlank;
import java.io.Serial;
import java.io.Serializable;
import java.time.DayOfWeek;
import java.util.EnumSet;
import java.util.Set;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;

/**
 * Represents a store or pickup location.
 * <p>
 * Stores address, contact information, and optional geolocation coordinates for
 * a physical Randy's location. One location may be designated as the primary location,
 * and visibility can be controlled independently. Equality is based solely on {@code id}.
 * </p>
 *
 * @see Order#locationId
 * @see PricingSheet
 */
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Location implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** Display name for this location. Required; must not be blank. */
  @NotBlank
  String name;

  /** Primary street address line. Required; must not be blank. */
  @NotBlank
  String address1;

  /** Secondary address line (suite, unit, etc.), or {@code null} if not applicable. */
  String address2;

  /** City. Required; must not be blank. */
  @NotBlank
  String city;

  /** State abbreviation (e.g., {@code "IL"}). Required; must not be blank. */
  @NotBlank
  String state;

  /** ZIP code. Required; must not be blank. */
  @NotBlank
  String zip;

  /** Contact phone number for this location. */
  String phone;

  /** Contact email address for this location. */
  String email;

  /** Whether this is the primary/default location. Defaults to {@code false}. */
  @Builder.Default
  boolean primaryLocation = false;

  /** Whether this location is visible. Defaults to {@code true}. */
  @Builder.Default
  boolean visible = true;

  /**
   * Days of the week on which this location does not accept pickup or delivery.
   * Defaults to an empty set, meaning every day is allowed.
   */
  @Builder.Default
  Set<DayOfWeek> disallowedDays = EnumSet.noneOf(DayOfWeek.class);

  /** Latitude coordinate for map integration, or {@code null} if not set. */
  private Double latitude;

  /** Longitude coordinate for map integration, or {@code null} if not set. */
  private Double longitude;

  /**
   * Returns whether geolocation coordinates are available for this location.
   *
   * @return {@code true} if both {@code latitude} and {@code longitude} are non-null
   */
  public boolean hasGeolocation() {
    return latitude != null && longitude != null;
  }
}
