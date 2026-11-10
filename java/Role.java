package com.sbsolutions.order.models;

/**
 * Enumeration representing user roles in the system.
 * <p>
 * This enum defines the authorization levels available to users. Roles are used throughout
 * the application to control access to various features and views via Spring Security
 * annotations such as {@code @RolesAllowed}.
 * </p>
 * <p>
 * The role hierarchy is:
 * </p>
 * <ul>
 *   <li>{@link #USER} - Standard user with access to basic functionality</li>
 *   <li>{@link #STAFF} - Staff member with access to operational features beyond standard users</li>
 *   <li>{@link #ADMIN} - Administrator with access to all functionality including administrative views</li>
 * </ul>
 *
 * @see User
 */
public enum Role {
  /**
   * Standard user role with access to basic application features.
   * Users with this role can browse products, place orders, and manage their shopping cart.
   */
  USER,

  /**
   * Administrator role with full access to all application features.
   * Administrators can manage users, access control views, and perform administrative tasks
   * in addition to all standard user capabilities.
   */
  ADMIN,

  /**
   * Staff role with access to operational features.
   * Staff members can manage orders and assist customers in addition to all standard user capabilities,
   * but do not have access to administrative configuration views.
   */
  STAFF
}
