package com.sbsolutions.order.models;

import java.io.Serializable;
import java.time.Instant;
import java.util.Set;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;

/**
 * Represents a user in the Order Administration system.
 * <p>
 * This class models user information derived from OAuth2 authentication and is persisted
 * to MongoDB. It serves as both a data transfer object for REST communication and an entity
 * for MongoDB storage.
 * </p>
 * <p>
 * User instances are created from OAuth2 provider attributes (Google) during authentication
 * and stored in MongoDB via the order-data REST service. The class implements {@link Serializable}
 * to support session persistence across application restarts.
 * </p>
 * <p>
 * User information includes:
 * </p>
 * <ul>
 *   <li>Email address (unique identifier from OAuth2 provider)</li>
 *   <li>First and last name from OAuth2 profile</li>
 *   <li>Profile picture URL from OAuth2 provider</li>
 *   <li>{@link Role} determined by application's admin list</li>
 *   <li>Individual {@link Permission}s granting fine-grained access beyond the user's role</li>
 *   <li>Geolocation data from last login (IP, city, country, coordinates)</li>
 *   <li>{@link #getLastLoginDeviceType() Device type} from last login (Mobile, Desktop, Tablet)</li>
 *   <li>Account creation and last updated timestamps</li>
 *   <li>Disabled flag for accounts suspended by an administrator</li>
 *   <li>Contact email and phone for order-related notifications</li>
 *   <li>Notification opt-in preference</li>
 *   <li>UI {@link #getTheme() theme preference} (light/dark)</li>
 * </ul>
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User implements Serializable {

  /**
   * User ID (MongoDB document ID).
   */
  @Id
  private String id;

  /**
   * The user's email address from their OAuth2 provider.
   * This serves as the unique business identifier for the user.
   */
  private String email;

  /**
   * The user's first name from their OAuth2 profile.
   */
  private String firstName;

  /**
   * The user's last name from their OAuth2 profile.
   */
  private String lastName;

  /**
   * URL to the user's profile picture from their OAuth2 provider.
   */
  private String picture;

  /**
   * The user's roles in the application (USER, STAFF, and/or ADMIN).
   * A user may hold multiple roles simultaneously.
   */
  private Set<Role> role;

  /**
   * Individual permissions granted to this user beyond their role.
   * <p>
   * Permissions allow fine-grained access control without changing the user's role. An
   * {@link Role#ADMIN} user implicitly has all permissions. A {@link Role#USER} or
   * {@link Role#STAFF} user only has the permissions explicitly listed here.
   * </p>
   */
  private Set<Permission> permissions;

  /**
   * The IP address from the user's last login.
   */
  private String lastLoginIp;

  /**
   * The city detected from the user's last login IP address.
   */
  private String lastLoginCity;

  /**
   * The country detected from the user's last login IP address.
   */
  private String lastLoginCountry;

  /**
   * The country code (ISO 3166-1 alpha-2) from the user's last login.
   */
  private String lastLoginCountryCode;

  /**
   * The latitude coordinate from the user's last login location.
   */
  private Double lastLoginLatitude;

  /**
   * The longitude coordinate from the user's last login location.
   */
  private Double lastLoginLongitude;

  /**
   * The timestamp of the user's last login.
   */
  private Instant lastLoginTimestamp;

  /**
   * The type of device used for the last login (e.g. "Mobile", "Desktop", "Tablet").
   */
  private String lastLoginDeviceType;

  /**
   * The raw User-Agent string from the last login.
   */
  private String lastLoginUserAgent;

  /**
   * The ID of the {@link Location} the user last selected or ordered from.
   */
  private String lastLocationId;

  /**
   * The timestamp when this user account was created.
   */
  @CreatedDate
  private Instant createdAt;

  /**
   * The timestamp when this user account was last updated.
   */
  @LastModifiedDate
  private Instant updatedAt;

  /**
   * Whether this account has been disabled by an administrator.
   * Disabled accounts cannot log in.
   */
  private boolean disabled;

  /**
   * A contact email address for this user, separate from their OAuth2 login email.
   * Used for order-related notifications and communications.
   */
  private String contactEmail;

  /**
   * A contact phone number for this user.
   * Used for order-related notifications and communications.
   */
  private String contactPhone;

  /**
   * Whether this user has opted in to notifications.
   * Defaults to {@code true}.
   */
  @Builder.Default
  private boolean allowNotifications = true;
  
  /**
   * The user's preferred UI theme (e.g. "light" or "dark").
   * Defaults to {@code "light"}.
   */
  @Builder.Default
  private String theme = "light";

  /**
   * Returns the user's full name by combining first and last name.
   *
   * @return the full name as "firstName lastName"
   */
  public String getFullName() {
    return firstName + " " + lastName;
  }

  /**
   * Returns a formatted string of the user's last login location.
   * <p>
   * If city and country are available, returns "City, Country".
   * If only country is available, returns "Country".
   * If no location data is available, returns "Unknown location".
   * </p>
   *
   * @return formatted location string
   */
  public String getLastLoginLocation() {
    if (lastLoginCity != null && lastLoginCountry != null) {
      return lastLoginCity + ", " + lastLoginCountry;
    } else if (lastLoginCountry != null) {
      return lastLoginCountry;
    }
    return "Unknown location";
  }

  /**
   * Checks if geolocation data is available for the last login.
   *
   * @return true if at least the IP address is available, false otherwise
   */
  public boolean hasGeolocationData() {
    return lastLoginIp != null;
  }
}
