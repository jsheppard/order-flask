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
 * Represents a customer in the ordering system.
 * <p>
 * Stores personal and contact information for a customer. Equality is based
 * solely on {@code id}.
 * </p>
 *
 * @see Order
 */
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class Customer implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /** MongoDB document ID. */
  @Id
  String id;

  /** Customer's first name. */
  String firstName;

  /** Customer's middle name, or {@code null} if not provided. */
  String middleName;

  /** Customer's last name. */
  String lastName;

  /** Primary street address line. */
  String address1;

  /** Secondary address line (apt, suite, etc.), or {@code null} if not applicable. */
  String address2;

  /** City. */
  String city;

  /** State abbreviation (e.g., {@code "IL"}). */
  String state;

  /** ZIP code. */
  String zip;

  /** Contact phone number. */
  String phone;

  /** Contact email address. */
  String email;
}
