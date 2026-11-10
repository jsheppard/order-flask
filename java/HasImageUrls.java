package com.sbsolutions.order.models;

/**
 * Interface for models that expose multiple image size variants.
 * <p>
 * Implementing classes (e.g., {@link Donut}) provide URLs for five standard image
 * sizes: original, medium, small, icon, and thumbnail. This allows UI components
 * to select the appropriate resolution without knowing the concrete type.
 * </p>
 *
 * @see Donut
 */
public interface HasImageUrls {

  /** Returns the URL for the full-resolution image. */
  String getImageOriginal();

  /** Returns the URL for the medium-resolution image. */
  String getImageMedium();

  /** Returns the URL for the small-resolution image. */
  String getImageSmall();

  /** Returns the URL for the icon-resolution image. */
  String getImageIcon();

  /** Returns the URL for the thumbnail image. */
  String getImageThumbnail();

  /** Sets the full-resolution image URL. */
  void setImageOriginal(String imageOriginal);

  /** Sets the medium-resolution image URL. */
  void setImageMedium(String imageMedium);

  /** Sets the small-resolution image URL. */
  void setImageSmall(String imageSmall);

  /** Sets the icon-resolution image URL. */
  void setImageIcon(String imageIcon);

  /** Sets the thumbnail image URL. */
  void setImageThumbnail(String imageThumbnail);

}
