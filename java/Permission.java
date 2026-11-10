package com.sbsolutions.order.models;

import java.util.Set;
import lombok.Getter;

/**
 * Granular permissions that can be assigned to individual users, independent of their role.
 * <p>
 * Permissions allow fine-grained access control beyond the three coarse-grained roles
 * ({@link Role#USER}, {@link Role#STAFF}, {@link Role#ADMIN}). A user with {@link Role#USER} may
 * be granted individual permissions that unlock specific admin or staff features without elevating
 * their entire role.
 * </p>
 * <p>
 * Permission checks are additive: {@link Role#ADMIN} implicitly has all permissions; a user passes
 * an access check if they hold the required role OR the required permission.
 * </p>
 *
 * @see User
 * @see Role
 */
@Getter
public enum Permission {

  // ── Product management ──────────────────────────────────────────────────────

  /**
   * Allows editing donuts, rolls, frostings, icings, and toppings menu items.
   */
  MANAGE_PRODUCTS("Manage Products", "Edit donuts, rolls, frostings, icings, and toppings", Set.of(Role.ADMIN)),

  // ── Administrative features ─────────────────────────────────────────────────

  /**
   * Allows accessing the User Management view and editing user accounts.
   */
  MANAGE_USERS("Manage Users", "Access user management and edit user accounts", Set.of(Role.ADMIN)),

  /**
   * Allows viewing and managing contact messages.
   */
  MANAGE_MESSAGES("Manage Messages", "Access and manage contact inquiries", Set.of(Role.ADMIN)),

  /**
   * Allows creating, editing, and managing sweepstakes contests.
   */
  MANAGE_SWEEPSTAKES("Manage Sweepstakes", "Create, edit, and manage promotional sweepstakes contests", Set.of(Role.ADMIN)),

  /**
   * Allows adding, editing, and removing locations.
   */
  MANAGE_LOCATIONS("Manage Locations", "Add, edit, and remove store locations", Set.of(Role.ADMIN)),

  /**
   * Allows controlling the display order of menu products.
   */
  MANAGE_PRODUCT_ORDERING("Manage Product Display Order", "Control display order of menu products", Set.of(Role.ADMIN)),

  /**
   * Allows viewing and editing the pricing sheet.
   */
  MANAGE_PRICING("Manage Pricing", "View and edit the pricing sheet", Set.of(Role.ADMIN)),

  /**
   * Allows accessing the scheduling configuration view.
   */
  MANAGE_SCHEDULE("Manage Schedule", "Access and modify scheduling configuration", Set.of(Role.ADMIN)),

  /**
   * Allows accessing the system messages configuration view for order statuses.
   */
  MANAGE_SYSTEM_MESSAGES("Manage System Messages", "Access and configure system messages for order statuses", Set.of(Role.ADMIN)),

  /**
   * Allows configuring item-type production limits.
   */
  MANAGE_LIMITS("Manage Limits", "Configure item-type production capacity limits"),

  /**
   * Allows reviewing and managing all customer orders.
   */
  REVIEW_ORDERS("Review Orders", "Access all orders review and management"),

  // ── Staff features ───────────────────────────────────────────────────────────

  /**
   * Allows setting and managing daily specials.
   */
  MANAGE_DAILY_SPECIAL("Manage Daily Special", "Set and manage daily specials"),

  /**
   * Allows accessing the production day planning view.
   */
  VIEW_PRODUCTION("View Production Day", "Access production day planning"),

  /**
   * Allows accessing the pickup/delivery order board.
   */
  VIEW_BOARD("View Pickup/Deliver", "Access the pickup/delivery order board"),

  // ── Statistics ───────────────────────────────────────────────────────────────

  /**
   * Allows viewing application statistics and metrics.
   */
  VIEW_STATS("View Statistics", "Access application statistics and metrics"),

  /**
   * Allows accessing the administrative dashboard.
   */
  VIEW_DASHBOARD("View Dashboard", "Access administrative dashboard with KPI charts", Set.of(Role.ADMIN)),

  /**
   * Allows accessing the system reports view.
   */
  VIEW_REPORTS("View Reports", "Access system reports and data exports", Set.of(Role.ADMIN)),

  /**
   * Allows viewing announcements and events calendar.
   */
  VIEW_ANNOUNCEMENTS("View Announcements", "Access announcements and events calendar");

  /**
   * Human-readable label suitable for display in the UI.
   * Includes the allowed roles in parentheses, e.g. {@code "Manage Products (ADMIN)"}.
   */
  private final String displayName;

  /**
   * Short description of what this permission allows.
   */
  private final String description;

  /**
   * The roles for which this permission is designated.
   * Admin-only permissions contain only {@link Role#ADMIN}; staff-accessible permissions
   * contain both {@link Role#STAFF} and {@link Role#ADMIN}.
   */
  private final Set<Role> allowedRoles;

  /**
   * Creates a permission with an explicit set of allowed roles.
   * The role names are appended to the display name in parentheses.
   *
   * @param displayName  human-readable label (roles will be appended)
   * @param description  short description of what the permission allows
   * @param allowedRoles roles for which this permission is designated
   */
  Permission(String displayName, String description, Set<Role> allowedRoles) {
    // append the roles to the display name
    if (!allowedRoles.isEmpty()) {
      this.displayName = displayName + " (%s)".formatted(String.join(", ", allowedRoles.stream().map(Role::name).toList()));
    } else {
      this.displayName = displayName;
    }
    this.description = description;
    this.allowedRoles = allowedRoles;
  }

  /**
   * Creates a permission accessible to both {@link Role#STAFF} and {@link Role#ADMIN}.
   * Both role names are appended to the display name in parentheses.
   *
   * @param displayName human-readable label (roles will be appended)
   * @param description short description of what the permission allows
   */
  Permission(String displayName, String description) {
    this.allowedRoles = Set.of(Role.STAFF, Role.ADMIN);
    // append the roles to the display name
    this.displayName = displayName + " (%s)".formatted(String.join(", ", allowedRoles.stream().map(Role::name).toList()));
    this.description = description;
  }
}
