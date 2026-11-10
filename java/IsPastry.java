package com.sbsolutions.order.models;

/**
 * Interface for pastry products that support customization options.
 * <p>
 * Defines properties for pastry items that can be customized with frosting,
 * icing, and topping options, along with flags to control availability and
 * mixing restrictions.
 * </p>
 */
public interface IsPastry {

  boolean isFrosting();

  void setFrosting(boolean frosting);

  boolean isRequiredFrosting();

  void setRequiredFrosting(boolean requiredFrosting);

  boolean isIcing();

  void setIcing(boolean icing);

  boolean isRequiredIcing();

  void setRequiredIcing(boolean requiredIcing);

  boolean isTopping();

  void setTopping(boolean topping);

  boolean isRequiredTopping();

  void setRequiredTopping(boolean requiredTopping);

  boolean isAllowMix();

  void setAllowMix(boolean allowMix);

}
