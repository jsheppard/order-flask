package com.sbsolutions.order.models.utils;

import java.lang.reflect.Field;
import java.text.NumberFormat;
import java.time.format.DateTimeFormatter;
import java.time.temporal.TemporalAccessor;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Utility class that generates a formatted bullet-point text summary from an object's
 * {@link BulletField}-annotated fields.
 * <p>
 * Use this class to produce human-readable, multi-line or single-line summaries of
 * model objects — for example, for display in notifications, admin views, or logs.
 * Fields are included only if annotated with {@link BulletField} and non-null. They
 * are sorted by {@link BulletField#order()} and formatted according to the annotation
 * attributes (currency, date pattern, multiline, emoji).
 * </p>
 * <p>
 * Nested objects are supported: if a field value is not a simple type, {@code generate}
 * is called recursively on the nested object.
 * </p>
 * <p>
 * Output is capped at {@value #MAX_LENGTH} characters.
 * </p>
 *
 * @see BulletField
 */
public class AdvancedBulletGenerator {

  private static final String BULLET = "\u2022 ";
  private static final int MAX_LENGTH = 1200;

  /**
   * Generates a multi-line bullet-point summary for the given object.
   * <p>
   * Equivalent to {@code generate(obj, false)}.
   * </p>
   *
   * @param obj the object to summarize; must have fields annotated with {@link BulletField}
   * @return formatted bullet-point string, capped at {@value #MAX_LENGTH} characters
   */
  public static String generate(Object obj) {
    return generate(obj, false);
  }

  /**
   * Generates a bullet-point summary for the given object, with an optional single-line mode.
   *
   * @param obj                the object to summarize; must have fields annotated with {@link BulletField}
   * @param singleLineFallback if {@code true}, newlines are replaced with spaces to produce a
   *                           single-line result
   * @return formatted bullet-point string, capped at {@value #MAX_LENGTH} characters
   */
  public static String generate(Object obj, boolean singleLineFallback) {

    List<Field> fields = new ArrayList<>();

    for (Field field : obj.getClass().getDeclaredFields()) {
      if (field.isAnnotationPresent(BulletField.class)) {
        fields.add(field);
      }
    }

    fields.sort(Comparator.comparingInt(
        f -> f.getAnnotation(BulletField.class).order()
    ));

    List<String> lines = new ArrayList<>();

    for (Field field : fields) {

      field.setAccessible(true);
      BulletField meta = field.getAnnotation(BulletField.class);

      try {

        Object value = field.get(obj);

        if (value == null) continue;

        String formatted = formatValue(value, meta);

        String prefix =
            BULLET +
                (meta.emoji().isEmpty() ? "" : meta.emoji() + " ") +
                meta.label() +
                ": ";

        if (meta.multiline()) {

          lines.add(prefix);
          lines.add(formatted);

        } else {

          lines.add(prefix + formatted);
        }

      } catch (Exception ignored) {
      }
    }

    String result = String.join("\n", lines);

    if (singleLineFallback) {
      result = result.replace("\n", " ");
    }

    if (result.length() > MAX_LENGTH) {
      result = result.substring(0, MAX_LENGTH);
    }

    return result;
  }

  private static String formatValue(Object value, BulletField meta) {

    if (meta.currency() && value instanceof Number) {
      return NumberFormat.getCurrencyInstance().format(value);
    }

    if (!meta.dateFormat().isEmpty() && value instanceof TemporalAccessor) {

      DateTimeFormatter formatter =
          DateTimeFormatter.ofPattern(meta.dateFormat());

      return formatter.format((TemporalAccessor) value);
    }

    if (isSimple(value)) {
      return value.toString();
    }

    return generate(value); // nested object support
  }

  private static boolean isSimple(Object obj) {

    return obj instanceof String ||
        obj instanceof Number ||
        obj instanceof Boolean ||
        obj instanceof Enum ||
        obj instanceof TemporalAccessor;
  }
}